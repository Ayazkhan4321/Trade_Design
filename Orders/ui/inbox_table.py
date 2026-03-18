from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLabel, QComboBox, QSizePolicy, QFrame, QStackedWidget
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtCore import Qt, QSize, QTimer 


class InboxTable(QWidget):
    """
    Inbox table matching the reference UI:
      - Subject / From / Time columns (Actions hidden until a row is selected)
      - Centred "No messages" placeholder when empty
      - Bottom bar: Rows-per-page selector (left) | Prev · Page X/Y · Next (right)
      - Full dynamic theming via ThemeManager
    """

    COLUMNS = [
        ("subject", "Subject"),
        ("from",    "From"),
        ("time",    "Time"),
        ("actions", "Actions"),
    ]

    _ROWS_OPTIONS = [10, 25, 50, 100]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._all_rows: list[dict] = []
        self._page      = 0           # current page index (0-based)
        self._rows_per  = 25          # rows per page

        # ── Outer layout ────────────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Stack: table vs empty placeholder ───────────────────────────
        self._stack = QStackedWidget(self)

        # Page 0 — table
        self.view = QTableView()
        self.view.setObjectName("inbox_table_view")
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.SingleSelection)
        self.view.verticalHeader().setVisible(False)
        self.view.setAlternatingRowColors(True)
        self.view.setFocusPolicy(Qt.NoFocus)
        self.view.setShowGrid(False)

        self.model = QStandardItemModel(0, len(self.COLUMNS), self)
        self.model.setHorizontalHeaderLabels([t for _, t in self.COLUMNS])
        self.view.setModel(self.model)

        header = self.view.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.view.horizontalHeader().hideSection(3)

        # "No messages" label floats over the table body (below the header)
        self._empty_lbl = QLabel("No messages", self.view)
        self._empty_lbl.setObjectName("inbox_empty_label")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._empty_lbl.hide()

        # Reposition label whenever view is resized
        self.view.installEventFilter(self)

        outer.addWidget(self.view, 1)

        # ── Divider ──────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setObjectName("inbox_divider")
        outer.addWidget(div)

        # ── Bottom bar ───────────────────────────────────────────────────
        self._bottom_bar = QWidget()
        self._bottom_bar.setObjectName("inbox_bottom_bar")
        self._bottom_bar.setFixedHeight(34)
        bb = QHBoxLayout(self._bottom_bar)
        bb.setContentsMargins(12, 0, 12, 0)
        bb.setSpacing(8)

        # Left: Rows label + combo
        rows_lbl = QLabel("Rows:")
        rows_lbl.setObjectName("inbox_rows_label")
        self._rows_combo = QComboBox()
        self._rows_combo.setObjectName("inbox_rows_combo")
        self._rows_combo.setFixedSize(60, 24)
        for opt in self._ROWS_OPTIONS:
            self._rows_combo.addItem(str(opt), opt)
        self._rows_combo.setCurrentIndex(self._ROWS_OPTIONS.index(self._rows_per))
        self._rows_combo.currentIndexChanged.connect(self._on_rows_changed)

        bb.addWidget(rows_lbl)
        bb.addWidget(self._rows_combo)
        bb.addStretch(1)

        # Right: Prev | Page X/Y | Next
        self._prev_btn = QPushButton("Prev")
        self._prev_btn.setObjectName("inbox_prev_btn")
        self._prev_btn.setFixedSize(48, 24)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.clicked.connect(self._on_prev)

        self._page_lbl = QLabel("Page 1 / 1")
        self._page_lbl.setObjectName("inbox_page_label")
        self._page_lbl.setAlignment(Qt.AlignCenter)
        self._page_lbl.setFixedWidth(90)

        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("inbox_next_btn")
        self._next_btn.setFixedSize(48, 24)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.clicked.connect(self._on_next)

        bb.addWidget(self._prev_btn)
        bb.addWidget(self._page_lbl)
        bb.addWidget(self._next_btn)

        outer.addWidget(self._bottom_bar)

        # ── Theme ────────────────────────────────────────────────────────
        self._apply_theme()
        try:
            from Theme.theme_manager import ThemeManager
            self._on_theme_cb = lambda n, t: self._apply_theme()
            ThemeManager.instance().theme_changed.connect(self._on_theme_cb)
        except Exception:
            pass

        self.setAttribute(Qt.WA_StyledBackground, True)
        self._refresh_view()

    # ── Theme ─────────────────────────────────────────────────────────────
    def _apply_theme(self):
        # Use the same proven pattern as BulkCloseDialog
        from PySide6.QtGui import QColor as _QColor
        from PySide6.QtWidgets import QApplication as _QApp

        def _detect_dark():
            try:
                from Theme.theme_manager import ThemeManager
                tok = ThemeManager.instance().tokens()
                val = tok.get("is_dark", None)
                if val is not None:
                    if isinstance(val, bool): return val
                    s = str(val).lower()
                    if s in ("true","1","yes","dark"): return True
                    if s in ("false","0","no","light"): return False
                for key in ("bg_panel","background","bg_primary","bg_base","bg"):
                    cs = tok.get(key)
                    if cs:
                        c = _QColor(cs)
                        if c.isValid(): return c.lightness() < 128
            except Exception: pass
            try:
                app = _QApp.instance()
                if app: return app.palette().window().color().lightness() < 128
            except Exception: pass
            return False

        dark = _detect_dark()
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
        except Exception:
            tok = {}

        def _t(*keys, fd, fl):
            for k in keys:
                v = tok.get(k)
                if v: return v
            return fd if dark else fl

        bg       = _t("bg_panel","background","bg_primary",fd="#151e2d",fl="#ffffff")
        bg_alt   = _t("bg_row_alt","bg_secondary","bg_surface",fd="#1a2535",fl="#f9fafb")
        bg_bar   = _t("bg_bottom_bar","bg_surface","bg_secondary",fd="#1a2535",fl="#f9fafb")
        hdr_bg   = _t("bg_table_header","bg_secondary","bg_surface",fd="#1e2a3a",fl="#f3f4f6")
        sel_bg   = _t("bg_tab_active","bg_selected","selection_bg",fd="#1a3a5c",fl="#e6f0ff")
        text     = _t("text_primary","text","fg",fd="#e2e8f0",fl="#111827")
        text_sec = _t("text_secondary","text_muted",fd="#94a3b8",fl="#6b7280")
        border   = _t("border","border_color","border_separator","divider",fd="#2d3a4a",fl="#e5e7eb")
        accent   = _t("accent","primary","color_accent",fd="#3b82f6",fl="#1976d2")
        btn_bg   = accent
        btn_text = "#ffffff"
        hdr_text = text_sec

        self.view.setStyleSheet(f"""
            QTableView {{
                background: {bg};
                alternate-background-color: {bg_alt};
                color: {text};
                border: none;
                gridline-color: transparent;
                font-size: 13px;
            }}
            QTableView::item:selected {{
                background: {sel_bg};
                color: {text};
            }}
            QTableView::item:hover {{ background: transparent; }}
            QHeaderView::section {{
                background: {hdr_bg};
                color: {hdr_text};
                font-size: 12px;
                font-weight: 600;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {border};
            }}
        """)

        self._empty_lbl.setStyleSheet(
            f"color: {text_sec}; font-size: 14px; background: transparent;"
        )

        self._bottom_bar.setStyleSheet(
            f"QWidget#inbox_bottom_bar {{"
            f"  background: {bg_bar};"
            f"  border-top: 1px solid {border};"
            f"}}"
        )

        label_style = f"color: {text}; font-size: 13px; background: transparent;"
        self.findChild(QLabel, "inbox_rows_label").setStyleSheet(label_style)
        self._page_lbl.setStyleSheet(label_style)

        self._rows_combo.setStyleSheet(f"""
            QComboBox {{
                background: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {bg};
                color: {text};
                selection-background-color: {sel_bg};
            }}
        """)

        nav_btn_style = f"""
            QPushButton {{
                background: {btn_bg};
                color: {btn_text};
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover   {{ background: {accent}; }}
            QPushButton:disabled {{
                background: {border};
                color: {text_sec};
            }}
        """
        self._prev_btn.setStyleSheet(nav_btn_style)
        self._next_btn.setStyleSheet(nav_btn_style)

        div = self.findChild(QFrame, "inbox_divider")
        if div:
            div.setStyleSheet(f"background-color: {border}; border: none; max-height: 1px; min-height: 1px;")

        # Outer widget bg — ensures no bleed-through from system default
        self.setStyleSheet(f"InboxTable {{ background-color: {bg}; border: none; }}")

    # ── Event filter: keep "No messages" centred in the table body ────────
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.view and event.type() == QEvent.Resize:
            self._position_empty_label()
        return False

    def _position_empty_label(self):
        hdr_h = self.view.horizontalHeader().height()
        w     = self.view.width()
        h     = self.view.height() - hdr_h
        self._empty_lbl.setGeometry(0, hdr_h, w, h)

    # ── Pagination helpers ────────────────────────────────────────────────
    def _total_pages(self) -> int:
        if not self._all_rows:
            return 1
        import math
        return math.ceil(len(self._all_rows) / self._rows_per)

    def _refresh_view(self):
        """Re-populate table for current page, update pagination controls."""
        total_pages = self._total_pages()
        self._page  = max(0, min(self._page, total_pages - 1))

        self._page_lbl.setText(f"Page {self._page + 1} / {total_pages}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(self._page < total_pages - 1)

        # Show/hide the "No messages" overlay
        if not self._all_rows:
            self._empty_lbl.show()
            self._empty_lbl.raise_()
            self._position_empty_label()
            self.model.removeRows(0, self.model.rowCount())
            return

        self._empty_lbl.hide()

        start     = self._page * self._rows_per
        page_rows = self._all_rows[start: start + self._rows_per]
        self.model.removeRows(0, self.model.rowCount())
        for r in page_rows:
            self._append_row(r)

    def _append_row(self, row: dict):
        items = []
        for key, _ in self.COLUMNS[:3]:
            val  = row.get(key, "") if isinstance(row, dict) else ""
            item = QStandardItem(str(val))
            item.setEditable(False)
            items.append(item)
        placeholder = QStandardItem("")
        placeholder.setEditable(False)
        items.append(placeholder)
        self.model.appendRow(items)

    # ── Slots ─────────────────────────────────────────────────────────────
    def _on_rows_changed(self, idx: int):
        self._rows_per = self._rows_combo.itemData(idx)
        self._page     = 0
        self._refresh_view()

    def _on_prev(self):
        if self._page > 0:
            self._page -= 1
            self._refresh_view()

    def _on_next(self):
        if self._page < self._total_pages() - 1:
            self._page += 1
            self._refresh_view()

    # ── Public API ────────────────────────────────────────────────────────
    def clear(self):
        self._all_rows.clear()
        self._page = 0
        self._refresh_view()

    def set_rows(self, rows):
        """Replace all rows. rows is a list of dicts with keys: subject, from, time."""
        self._all_rows = list(rows or [])
        self._page     = 0
        self._refresh_view()

    def add_row(self, row: dict):
        """Append a single row and refresh the current page."""
        self._all_rows.append(row)
        self._refresh_view()

    def get_selected(self):
        idx = self.view.selectionModel().currentIndex()
        if not idx.isValid():
            return None
        row = idx.row()
        data = {}
        for col, (key, _) in enumerate(self.COLUMNS):
            item = self.model.item(row, col)
            data[key] = item.text() if item else ""
        return data