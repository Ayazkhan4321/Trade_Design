"""
logs_table.py  –  Logs tab widget for the Orders UI.

Columns  : TIMESTAMP ↓ | ACTION | TYPE | DESCRIPTION | CREATED BY | RESULT
Features :
  • ACTION cell rendered as a coloured label (blue link style)
  • RESULT cell rendered as a coloured badge  (green = SUCCESS, red = FAILED, etc.)
  • Sortable TIMESTAMP column (descending by default)
  • Bottom bar  : Rows-per-page selector (left)  |  Prev · Page X/Y · Next (right)
  • Full dynamic theming via ThemeManager
"""

from __future__ import annotations

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QSizePolicy, QFrame,
    QAbstractItemView,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt

# ── Column indices ────────────────────────────────────────────────────────────
COL_TIMESTAMP  = 0
COL_ACTION     = 1
COL_TYPE       = 2
COL_DESCRIPTION = 3
COL_CREATED_BY = 4
COL_RESULT     = 5

HEADERS = ["TIMESTAMP ↓", "ACTION", "TYPE", "DESCRIPTION", "CREATED BY", "RESULT"]

_ROWS_OPTIONS = [10, 25, 50, 100]

# Colour map for ACTION text
_ACTION_COLORS: dict[str, str] = {
    "login":    "#3b9eff",
    "logout":   "#3b9eff",
    "buy":      "#22c55e",
    "sell":     "#ef4444",
    "deposit":  "#a855f7",
    "withdraw": "#f59e0b",
}

# Colour map for RESULT badge
_RESULT_COLORS: dict[str, tuple[str, str]] = {   # (text_color, bg_color)
    "success": ("#16a34a", "#dcfce7"),
    "failed":  ("#dc2626", "#fee2e2"),
    "error":   ("#dc2626", "#fee2e2"),
    "pending": ("#d97706", "#fef3c7"),
    "rejected":("#dc2626", "#fee2e2"),
}


class LogsTable(QWidget):
    """
    Logs table widget.

    Public API
    ----------
    set_rows(rows)   – replace all rows; each row is a dict with keys:
                       timestamp, action, type, description, created_by, result
    add_row(row)     – append a single row dict and refresh
    clear()          – remove all rows
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self._all_rows: list[dict] = []
        self._page     = 0
        self._rows_per = 25

        # ── Outer layout ─────────────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget(0, len(HEADERS))
        self.table.setObjectName("logs_table_view")
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(COL_TIMESTAMP, Qt.DescendingOrder)

        hdr = self.table.horizontalHeader()
        hdr.setHighlightSections(False)
        hdr.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hdr.setSectionResizeMode(COL_TIMESTAMP,   QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_ACTION,      QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_TYPE,        QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_DESCRIPTION, QHeaderView.Stretch)
        hdr.setSectionResizeMode(COL_CREATED_BY,  QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_RESULT,      QHeaderView.ResizeToContents)

        # Vertical row height
        self.table.verticalHeader().setDefaultSectionSize(32)

        outer.addWidget(self.table, 1)

        # ── Divider ───────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setObjectName("logs_divider")
        outer.addWidget(div)

        # ── Bottom bar ────────────────────────────────────────────────────
        self._bottom_bar = QWidget()
        self._bottom_bar.setObjectName("logs_bottom_bar")
        self._bottom_bar.setFixedHeight(36)
        bb = QHBoxLayout(self._bottom_bar)
        bb.setContentsMargins(12, 0, 12, 0)
        bb.setSpacing(8)

        # Left: Rows label + combo
        rows_lbl = QLabel("Rows:")
        rows_lbl.setObjectName("logs_rows_label")
        self._rows_combo = QComboBox()
        self._rows_combo.setObjectName("logs_rows_combo")
        self._rows_combo.setFixedSize(64, 26)
        for opt in _ROWS_OPTIONS:
            self._rows_combo.addItem(str(opt), opt)
        self._rows_combo.setCurrentIndex(_ROWS_OPTIONS.index(self._rows_per))
        self._rows_combo.currentIndexChanged.connect(self._on_rows_changed)

        bb.addWidget(rows_lbl)
        bb.addWidget(self._rows_combo)
        bb.addStretch(1)

        # Right: Prev | Page X/Y | Next
        self._prev_btn = QPushButton("Prev")
        self._prev_btn.setObjectName("logs_prev_btn")
        self._prev_btn.setFixedSize(52, 26)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.clicked.connect(self._on_prev)

        self._page_lbl = QLabel("Page 1 / 1")
        self._page_lbl.setObjectName("logs_page_label")
        self._page_lbl.setAlignment(Qt.AlignCenter)
        self._page_lbl.setFixedWidth(90)

        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("logs_next_btn")
        self._next_btn.setFixedSize(52, 26)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.clicked.connect(self._on_next)

        bb.addWidget(self._prev_btn)
        bb.addWidget(self._page_lbl)
        bb.addWidget(self._next_btn)

        outer.addWidget(self._bottom_bar)

        # ── Theme ─────────────────────────────────────────────────────────
        self._apply_theme()
        try:
            from Theme.theme_manager import ThemeManager
            self._on_theme_changed = lambda n, t: self._apply_theme()
            ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
        except Exception:
            pass

        self._refresh_view()

    # ── Theming ────────────────────────────────────────────────────────────
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

        self._is_dark = dark

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {bg};
                alternate-background-color: {bg_alt};
                color: {text};
                border: none;
                gridline-color: transparent;
                font-size: 13px;
                outline: 0;
            }}
            QTableWidget::item {{
                padding: 0px 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {sel_bg};
                color: {text};
            }}
            QTableWidget::item:hover {{
                background: transparent;
            }}
            QHeaderView::section {{
                background: {hdr_bg};
                color: {hdr_text};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {border};
                border-right: 1px solid {border};
                text-transform: uppercase;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
            QScrollBar:vertical {{
                background: {bg_alt};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {border};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self._bottom_bar.setStyleSheet(f"""
            QWidget#logs_bottom_bar {{
                background: {bg_bar};
                border-top: 1px solid {border};
            }}
        """)

        lbl_style = f"color: {text}; font-size: 13px; background: transparent;"
        for obj_name in ("logs_rows_label", "logs_page_label"):
            lbl = self.findChild(QLabel, obj_name)
            if lbl:
                lbl.setStyleSheet(lbl_style)

        self._rows_combo.setStyleSheet(f"""
            QComboBox {{
                background: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox QAbstractItemView {{
                background: {bg};
                color: {text};
                selection-background-color: {sel_bg};
                border: 1px solid {border};
            }}
        """)

        nav_style = f"""
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
        self._prev_btn.setStyleSheet(nav_style)
        self._next_btn.setStyleSheet(nav_style)

        div = self.findChild(QFrame, "logs_divider")
        if div:
            div.setStyleSheet(f"background-color: {border}; border: none; max-height: 1px;")

        # Outer widget background (so it matches panel, not system default)
        self.setStyleSheet(f"""
            LogsTable, QWidget#logs_outer {{
                background-color: {bg};
                border: none;
            }}
        """)

        # Re-paint existing rows to pick up new badge colours
        self._repaint_badge_cells()

    # ── Helpers ────────────────────────────────────────────────────────────
    def _total_pages(self) -> int:
        return max(1, math.ceil(len(self._all_rows) / self._rows_per))

    def _refresh_view(self):
        total = self._total_pages()
        self._page = max(0, min(self._page, total - 1))

        self._page_lbl.setText(f"Page {self._page + 1} / {total}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(self._page < total - 1)

        start     = self._page * self._rows_per
        page_rows = self._all_rows[start: start + self._rows_per]

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row in page_rows:
            self._append_row(row)
        self.table.setSortingEnabled(True)

    def _append_row(self, row: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, 32)

        # ── TIMESTAMP ──────────────────────────────────────────────────
        ts_item = QTableWidgetItem(str(row.get("timestamp", "")))
        ts_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.table.setItem(r, COL_TIMESTAMP, ts_item)

        # ── ACTION (coloured text) ─────────────────────────────────────
        action     = str(row.get("action", ""))
        action_key = action.lower()
        act_color  = _ACTION_COLORS.get(action_key, "#3b9eff")

        act_item = QTableWidgetItem(action)
        act_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        act_item.setForeground(QColor(act_color))
        fnt = act_item.font()
        fnt.setBold(True)
        act_item.setFont(fnt)
        self.table.setItem(r, COL_ACTION, act_item)

        # ── TYPE ───────────────────────────────────────────────────────
        type_item = QTableWidgetItem(str(row.get("type", "")))
        type_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.table.setItem(r, COL_TYPE, type_item)

        # ── DESCRIPTION ────────────────────────────────────────────────
        desc_item = QTableWidgetItem(str(row.get("description", "")))
        desc_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.table.setItem(r, COL_DESCRIPTION, desc_item)

        # ── CREATED BY ─────────────────────────────────────────────────
        created_item = QTableWidgetItem(str(row.get("created_by", "")))
        created_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.table.setItem(r, COL_CREATED_BY, created_item)

        # ── RESULT (badge) ─────────────────────────────────────────────
        result     = str(row.get("result", ""))
        result_key = result.lower()
        text_c, bg_c = _RESULT_COLORS.get(result_key, ("#16a34a", "#dcfce7"))
        if getattr(self, "_is_dark", False):
            # Use solid foreground colour only in dark mode (no background badge)
            res_item = QTableWidgetItem(result.upper())
            res_item.setForeground(QColor(text_c))
        else:
            res_item = QTableWidgetItem(result.upper())
            res_item.setForeground(QColor(text_c))

        res_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        rfnt = res_item.font()
        rfnt.setBold(True)
        res_item.setFont(rfnt)
        self.table.setItem(r, COL_RESULT, res_item)

    def _repaint_badge_cells(self):
        """Update ACTION / RESULT cell colours after a theme change."""
        for r in range(self.table.rowCount()):
            act_item = self.table.item(r, COL_ACTION)
            if act_item:
                key   = act_item.text().lower()
                color = _ACTION_COLORS.get(key, "#3b9eff")
                act_item.setForeground(QColor(color))

            res_item = self.table.item(r, COL_RESULT)
            if res_item:
                key      = res_item.text().lower()
                text_c, _ = _RESULT_COLORS.get(key, ("#16a34a", "#dcfce7"))
                res_item.setForeground(QColor(text_c))

    # ── Slots ──────────────────────────────────────────────────────────────
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

    # ── Public API ─────────────────────────────────────────────────────────
    def clear(self):
        self._all_rows.clear()
        self._page = 0
        self._refresh_view()

    def set_rows(self, rows: list[dict]):
        """Replace all rows. Each dict must have keys:
        timestamp, action, type, description, created_by, result
        """
        self._all_rows = list(rows or [])
        self._page     = 0
        self._refresh_view()

    def add_row(self, row: dict):
        """Prepend a single row (newest first) and refresh."""
        self._all_rows.insert(0, row)
        self._refresh_view()

    def closeEvent(self, event):
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.disconnect(self._on_theme_changed)
        except Exception:
            pass
        super().closeEvent(event)