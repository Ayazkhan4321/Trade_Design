from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QScrollBar, QSizePolicy
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtCore import Qt, QTimer

from .bottom_bar import HistoryBottomBar

# Minimum pixel widths per column header label
_HIST_COL_MIN_WIDTH = {
    "ID":           75,
    "TIME":        135,
    "TYPE":         60,
    "SYMBOL":       75,
    "LOT SIZE":     75,
    "ENTRY PRICE":  95,
    "ENTRY VALUE":  95,
    "S/L":          55,
    "T/P":          55,
    "CLOSED TIME": 135,
    "CLOSED PRICE":105,
    "CLOSED VALUE":105,
    "COMMISSION":   95,
    "SWAP":         65,
    "PROFIT/LOSS":  95,
    "P/L IN %":     85,
    "REMARK":      110,
}
_DEFAULT_MIN = 80


def _col_min(name: str) -> int:
    return _HIST_COL_MIN_WIDTH.get(name.strip().upper(), _DEFAULT_MIN)


class HistoryTable(QWidget):
    COLUMNS = [
        ("id",           "ID"),
        ("time",         "TIME"),
        ("type",         "TYPE"),
        ("symbol",       "SYMBOL"),
        ("lot",          "LOT SIZE"),
        ("entry_price",  "ENTRY PRICE"),
        ("entry_value",  "ENTRY VALUE"),
        ("sl",           "S/L"),
        ("tp",           "T/P"),
        ("closed_time",  "CLOSED TIME"),
        ("closed_price", "CLOSED PRICE"),
        ("closed_value", "CLOSED VALUE"),
        ("commission",   "COMMISSION"),
        ("swap",         "SWAP"),
        ("pl",           "PROFIT/LOSS"),
        ("pl_pct",       "P/L IN %"),
        ("remarks",      "REMARK"),
    ]
    # Column header strings in order — used by _redistribute_column_widths
    _HEADERS = [title for _, title in COLUMNS]

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Table view + model ──────────────────────────────────────────
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(0, len(self.COLUMNS), self)
        self.model.setHorizontalHeaderLabels(self._HEADERS)
        self.table_view.setModel(self.model)

        # ── Table behaviour ─────────────────────────────────────────────
        self.table_view.setObjectName("history_table_view")
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setFocusPolicy(Qt.NoFocus)
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # ── Selection / hover styling ───────────────────────────────────
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            self._apply_style(t)
            def _on_theme(name, tok):
                try:
                    self._apply_style(tok)
                except RuntimeError:
                    pass
            ThemeManager.instance().theme_changed.connect(_on_theme)
        except Exception:
            self._apply_style(None)

        # ── Header ──────────────────────────────────────────────────────
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)   # our logic owns all widths
        header.setMinimumSectionSize(50)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(28)
        header.setHighlightSections(False)

        # History has no fixed-width delegate columns
        self._fixed_cols = set()

        # ── Bottom bar ──────────────────────────────────────────────────
        self.bottom_bar = HistoryBottomBar(self)

        # ── Custom horizontal scrollbar (mirrors OrderTable exactly) ────
        self.h_scrollbar = QScrollBar(Qt.Horizontal, self)
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        internal_bar = self.table_view.horizontalScrollBar()
        internal_bar.rangeChanged.connect(self.h_scrollbar.setRange)
        internal_bar.valueChanged.connect(self.h_scrollbar.setValue)
        self.h_scrollbar.valueChanged.connect(internal_bar.setValue)
        internal_bar.rangeChanged.connect(
            lambda mn, mx: self.h_scrollbar.setVisible(mx > 0))

        # ── Layout (identical structure to OrderTable) ──────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.table_view)
        layout.addWidget(self.bottom_bar)
        layout.addStretch(1)
        layout.addWidget(self.h_scrollbar)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Model signals ───────────────────────────────────────────────
        self.model.rowsInserted.connect(lambda p, f, l: self._update_table_height())
        self.model.rowsInserted.connect(lambda p, f, l: self._update_bottom_bar())
        self.model.rowsRemoved.connect(lambda p, f, l: self._update_table_height())
        self.model.rowsRemoved.connect(lambda p, f, l: self._update_bottom_bar())
        self.model.modelReset.connect(self._update_table_height)
        self.model.modelReset.connect(self._update_bottom_bar)
        self.model.layoutChanged.connect(self._update_table_height)
        self.model.layoutChanged.connect(self._update_bottom_bar)
        self.model.dataChanged.connect(lambda tl, br, r: self._update_bottom_bar())

        # ── Startup (mirrors OrderTable timers exactly) ─────────────────
        QTimer.singleShot(0,   self._update_table_height)
        QTimer.singleShot(0,   self._redistribute_column_widths)
        QTimer.singleShot(200, self._update_bottom_bar)

    # ── Style ────────────────────────────────────────────────────────────
    def _apply_style(self, tok):
        bg_select  = tok.get('bg_tab_active', '#e6f0ff') if tok else '#e6f0ff'
        text_color = tok.get('text_primary',  '#1a202c') if tok else '#1a202c'
        hover_bg   = tok.get('bg_row_hover',  'transparent') if tok else 'transparent'
        self.table_view.setStyleSheet(
            f"QTableView::item:hover    {{ background: {hover_bg}; }}"
            f"QTableView::item:focus    {{ outline: none; }}"
            f"QTableView::item:selected {{ background: {bg_select}; color: {text_color}; }}"
            f"QTableView                {{ border: none; gridline-color: transparent; }}"
        )

    # ── Bottom bar updater ───────────────────────────────────────────────
    def _update_bottom_bar(self):
        """
        Walks the model rows and sums commission and P&L.
        Deposits / Withdrawals are financial account-level values — pass them
        in via set_deposits() / set_withdrawals() from the account service.
        """
        try:
            col_map = {key: idx for idx, (key, _) in enumerate(self.COLUMNS)}
            pl_col   = col_map.get("pl",         -1)
            comm_col = col_map.get("commission",  -1)

            total_pl   = 0.0
            total_comm = 0.0

            for row in range(self.model.rowCount()):
                if pl_col >= 0:
                    try:
                        total_pl += float(
                            self.model.item(row, pl_col).text() or 0)
                    except (ValueError, AttributeError):
                        pass
                if comm_col >= 0:
                    try:
                        total_comm += float(
                            self.model.item(row, comm_col).text() or 0)
                    except (ValueError, AttributeError):
                        pass

            self.bottom_bar.set_net_pl(total_pl)
            self.bottom_bar.set_commission(total_comm)
        except Exception:
            pass

    # ── Public setters for account-level values ──────────────────────────
    def set_currency(self, currency: str):
        self.bottom_bar.set_currency(currency)

    def set_deposits(self, value: float):
        self.bottom_bar.set_deposits(value)

    def set_withdrawals(self, value: float):
        self.bottom_bar.set_withdrawals(value)

    # ── Column show/hide (exact OrderTable logic) ────────────────────────
    def toggle_column(self, col_index: int, visible: bool):
        try:
            header = self.table_view.horizontalHeader()
            if visible:
                header.showSection(col_index)
            else:
                header.hideSection(col_index)
            QTimer.singleShot(30, self._redistribute_column_widths)
        except Exception:
            pass

    # ── Column width redistribution (exact OrderTable logic) ─────────────
    def _redistribute_column_widths(self):
        try:
            header     = self.table_view.horizontalHeader()
            total_cols = header.count()
            viewport_w = self.table_view.viewport().width()

            if viewport_w <= 0:
                return

            fixed_w = sum(
                self.table_view.columnWidth(i)
                for i in self._fixed_cols
                if not header.isSectionHidden(i)
            )
            flex_cols = [
                i for i in range(total_cols)
                if i not in self._fixed_cols and not header.isSectionHidden(i)
            ]
            if not flex_cols:
                return

            available_w = max(0, viewport_w - fixed_w)
            n           = len(flex_cols)
            min_widths  = [_col_min(self._HEADERS[i]) for i in flex_cols]
            total_min   = sum(min_widths)

            if available_w <= total_min:
                for col_i, mw in zip(flex_cols, min_widths):
                    self.table_view.setColumnWidth(col_i, mw)
                return

            surplus    = available_w - total_min
            extra_each = surplus // n
            remainder  = surplus - extra_each * n

            for idx, (col_i, mw) in enumerate(zip(flex_cols, min_widths)):
                extra = extra_each + (remainder if idx == n - 1 else 0)
                self.table_view.setColumnWidth(col_i, mw + extra)
        except Exception:
            pass

    # ── Table height (exact OrderTable logic — bottom_bar.height() subtracted)
    def _update_table_height(self):
        try:
            header_h  = self.table_view.horizontalHeader().height()
            rows_h    = self.table_view.verticalHeader().length()
            frame_w   = self.table_view.frameWidth() * 2
            content_h = header_h + rows_h + frame_w
            if self.model.rowCount() == 0:
                content_h = header_h + frame_w

            scroll_h    = self.h_scrollbar.height() if self.h_scrollbar.isVisible() else 0
            # ← KEY: subtract bottom_bar just like OrderTable does
            available_h = self.height() - self.bottom_bar.height() - scroll_h
            if available_h <= 0:
                available_h = 200

            final_h = max(min(content_h, available_h), header_h + frame_w)
            self.table_view.setFixedHeight(final_h)
        except Exception:
            pass

    # ── Resize ───────────────────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_table_height()
        QTimer.singleShot(0, self._redistribute_column_widths)

    # ── Data helpers ─────────────────────────────────────────────────────
    def set_rows(self, rows):
        self.model.removeRows(0, self.model.rowCount())
        for r in rows or []:
            self.add_row(r)
        QTimer.singleShot(0, self._update_table_height)
        QTimer.singleShot(0, self._redistribute_column_widths)

    def add_row(self, row: dict):
        items = []
        for key, _ in self.COLUMNS:
            val = row.get(key, "") if isinstance(row, dict) else ""
            if key == "id":
                try:    cell = str(int(float(val))) if val else ""
                except: cell = str(val)
            else:
                try:    cell = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
                except: cell = str(val)

            it = QStandardItem(cell)
            it.setEditable(False)
            it.setTextAlignment(Qt.AlignCenter)

            if key == "type":
                v = str(val).lower()
                if "buy"    in v: it.setForeground(QColor("#22C55E"))
                elif "sell" in v: it.setForeground(QColor("#EF4444"))
            if key in ("pl", "pl_pct"):
                try:
                    num = float(val)
                    it.setForeground(QColor("#22C55E" if num >= 0 else "#EF4444"))
                except:
                    pass
            items.append(it)
        self.model.appendRow(items)