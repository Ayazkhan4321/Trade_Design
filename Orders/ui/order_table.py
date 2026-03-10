from PySide6.QtWidgets import (
    QWidget,
    QTableView,
    QSizePolicy,
    QVBoxLayout,
    QHeaderView,
    QMenu,
    QScrollBar
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QCursor, QAction
from .bulk_close_dialog import BulkCloseDialog

from ..models.order_model import OrderModel
from .bottom_bar import BottomBar

from .delegates.action_delegate import CloseDelegate
from .delegates.remark_delegate import RemarkDelegate


# Minimum pixel width so each header label is fully visible
_COL_MIN_WIDTH = {
    "ID":           50,
    "TIME":        130,
    "TYPE":         58,
    "SYMBOL":       72,
    "LOT SIZE":     72,
    "LOT":          58,
    "ENTRY PRICE":  95,
    "ENTRY VALUE":  95,
    "S/L":          50,
    "T/P":          50,
    "MARKET PRICE":105,
    "MARKET VALUE":105,
    "SWAP":         62,
    "COMMISSION":  100,
    "PROFIT/LOSS":  90,
    "P/L IN %":     78,
    "P/L%":         68,
}
_DEFAULT_MIN = 80


def _col_min(name: str) -> int:
    return _COL_MIN_WIDTH.get(name.strip().upper(), _DEFAULT_MIN)


class OrderTable(QWidget):
    def __init__(self, order_service=None):
        super().__init__()

        # -----------------------------
        # Table view + model
        # -----------------------------
        self.table_view = QTableView(self)
        self.model = OrderModel()
        try:
            self.model.order_service = order_service
        except Exception:
            pass
        self.table_view.setModel(self.model)

        # -----------------------------
        # Table behavior
        # -----------------------------
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)

        try:
            self.table_view.setMouseTracking(True)
            self.table_view.installEventFilter(self)
        except Exception:
            pass

        try:
            self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        except Exception:
            pass

        # Selection / hover styling
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            self.table_view.setFocusPolicy(Qt.NoFocus)
            light_select_bg = t.get('bg_tab_active', '#e6f0ff')
            text_color      = t.get('text_primary',  '#1a202c')
            self.table_view.setStyleSheet(
                f"QTableView::item:hover {{ background: {t.get('bg_row_hover', 'transparent')}; }}"
                f"QTableView::item:focus {{ outline: none; }}"
                f"QTableView::item:selected {{ background: {light_select_bg}; color: {text_color}; }}"
            )
            def _on_theme_changed(name, tok, tv=self.table_view):
                try:
                    tv.setStyleSheet(
                        f"QTableView::item:hover {{ background: {tok.get('bg_row_hover','transparent')}; }}"
                        f"QTableView::item:focus {{ outline: none; }}"
                        f"QTableView::item:selected {{ background: {tok.get('bg_tab_active','#e6f0ff')};"
                        f" color: {tok.get('text_primary','#1a202c')}; }}"
                    )
                except RuntimeError:
                    pass
            ThemeManager.instance().theme_changed.connect(_on_theme_changed)
        except Exception:
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.setStyleSheet(
                "QTableView::item:hover { background: transparent; }"
                "QTableView::item:focus { outline: none; }"
                "QTableView::item:selected { background: #e6f0ff; color: #1a202c; }"
            )

        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # -----------------------------
        # Header configuration
        # -----------------------------
        header  = self.table_view.horizontalHeader()
        headers = self.model.headers

        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(50)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(28)

        # -----------------------------
        # Delegates
        # -----------------------------
        def _find_index(candidates, fallback_index):
            for c in candidates:
                try:
                    return headers.index(c)
                except ValueError:
                    continue
            if fallback_index < 0:
                idx = len(headers) + fallback_index
                if 0 <= idx < len(headers):
                    return idx
            return 0

        action_col = _find_index(["Actions", "Options ⋮", "Options", "⋮"], -2)
        remark_col = _find_index(["Remarks", "Remark"], -1)

        try:
            self.model.headers[action_col] = "Actions  ⋮"
            header.repaint()
        except Exception:
            pass

        self.table_view.setItemDelegateForColumn(
            action_col,
            CloseDelegate(self.table_view, order_service=order_service)
        )
        self.table_view.setItemDelegateForColumn(
            remark_col,
            RemarkDelegate(self.table_view)
        )

        # Actions + Remarks: fixed width, never touched by redistribution
        header.setSectionResizeMode(action_col, QHeaderView.Fixed)
        header.setSectionResizeMode(remark_col, QHeaderView.Fixed)
        self.table_view.setColumnWidth(action_col, 90)
        self.table_view.setColumnWidth(remark_col, 80)

        self._fixed_cols = {action_col, remark_col}

        # -----------------------------
        # Bottom bar
        # -----------------------------
        self.profit_col = headers.index("PROFIT/LOSS")
        self.bottom_bar = BottomBar(self.table_view, self.profit_col)

        # -----------------------------
        # Layout + custom scrollbar
        # -----------------------------
        self.h_scrollbar = QScrollBar(Qt.Horizontal, self)
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        internal_bar = self.table_view.horizontalScrollBar()
        internal_bar.rangeChanged.connect(self.h_scrollbar.setRange)
        internal_bar.valueChanged.connect(self.h_scrollbar.setValue)
        self.h_scrollbar.valueChanged.connect(internal_bar.setValue)
        internal_bar.rangeChanged.connect(
            lambda mn, mx: self.h_scrollbar.setVisible(mx > 0)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.table_view)
        layout.addWidget(self.bottom_bar)
        layout.addStretch(1)
        layout.addWidget(self.h_scrollbar)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Header click (bulk-close dialog on Actions column)
        try:
            header.setSectionsClickable(True)
            def _on_header_clicked(section):
                try:
                    if section != action_col:
                        return
                    try:
                        dlg = BulkCloseDialog(
                            self,
                            order_service=getattr(self.model, 'order_service', None),
                            model=self.model
                        )
                        dlg.exec()
                    except Exception:
                        menu = QMenu(self)
                        a1 = QAction("Options", self)
                        menu.addAction(a1)
                        a1.triggered.connect(lambda: print("Header Options clicked"))
                        menu.exec(QCursor.pos())
                except Exception:
                    pass
            header.sectionClicked.connect(_on_header_clicked)
        except Exception:
            pass

        try:
            self.model.rowsInserted.connect(lambda p, f, l: self._update_table_height())
            self.model.rowsRemoved.connect(lambda p, f, l: self._update_table_height())
            self.model.modelReset.connect(self._update_table_height)
            self.model.layoutChanged.connect(self._update_table_height)
        except Exception:
            pass

        QTimer.singleShot(0, self._update_table_height)
        QTimer.singleShot(0, self._redistribute_column_widths)

    # ------------------------------------------------------------------
    # PUBLIC: the ONE entry point for show/hide — always redistributes
    # ------------------------------------------------------------------
    def toggle_column(self, col_index: int, visible: bool):
        """Show or hide a column, then redistribute widths so all
        remaining columns fill the viewport with no empty space."""
        try:
            header = self.table_view.horizontalHeader()
            if visible:
                header.showSection(col_index)
            else:
                header.hideSection(col_index)
            # Defer 30 ms so Qt finishes updating section geometry first
            QTimer.singleShot(30, self._redistribute_column_widths)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Redistribute: give each column its minimum width first, then share
    # leftover space equally — no empty gap, no truncated headers.
    # ------------------------------------------------------------------
    def _redistribute_column_widths(self):
        try:
            header     = self.table_view.horizontalHeader()
            headers    = self.model.headers
            total_cols = header.count()
            viewport_w = self.table_view.viewport().width()

            if viewport_w <= 0:
                return

            # Space consumed by fixed (pinned) visible columns
            fixed_w = sum(
                self.table_view.columnWidth(i)
                for i in self._fixed_cols
                if not header.isSectionHidden(i)
            )

            # All visible, non-fixed flex columns
            flex_cols = [
                i for i in range(total_cols)
                if i not in self._fixed_cols
                and not header.isSectionHidden(i)
            ]
            if not flex_cols:
                return

            available_w = max(0, viewport_w - fixed_w)
            n           = len(flex_cols)
            min_widths  = [_col_min(headers[i]) for i in flex_cols]
            total_min   = sum(min_widths)

            if available_w <= total_min:
                # Window too narrow — give minimums, scrollbar appears
                for col_i, mw in zip(flex_cols, min_widths):
                    self.table_view.setColumnWidth(col_i, mw)
                return

            # Share surplus space equally on top of each column's minimum
            surplus    = available_w - total_min
            extra_each = surplus // n
            remainder  = surplus - extra_each * n

            for idx, (col_i, mw) in enumerate(zip(flex_cols, min_widths)):
                extra = extra_each + (remainder if idx == n - 1 else 0)
                self.table_view.setColumnWidth(col_i, mw + extra)

        except Exception:
            pass

    # ------------------------------------------------------------------
    # Dynamic height — snaps table to row count
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_table_height()
        QTimer.singleShot(0, self._redistribute_column_widths)

    def _update_table_height(self):
        try:
            header_h = self.table_view.horizontalHeader().height()
            rows_h   = self.table_view.verticalHeader().length()
            frame_w  = self.table_view.frameWidth() * 2

            content_h = header_h + rows_h + frame_w
            if self.model.rowCount() == 0:
                content_h = header_h + frame_w

            scroll_h    = self.h_scrollbar.height() if self.h_scrollbar.isVisible() else 0
            available_h = self.height() - self.bottom_bar.height() - scroll_h
            if available_h <= 0:
                available_h = 200

            final_h = min(content_h, available_h)
            final_h = max(final_h, header_h + frame_w)
            self.table_view.setFixedHeight(final_h)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if obj is self.table_view:
                if event.type() == QEvent.Leave:
                    try:
                        self.table_view.clearSelection()
                    except Exception:
                        pass
                    return False
                if event.type() == QEvent.MouseMove:
                    pos = event.pos()
                    idx = self.table_view.indexAt(pos)
                    if not idx.isValid():
                        try:
                            self.table_view.clearSelection()
                        except Exception:
                            pass
                    return False
                if event.type() == QEvent.FocusOut:
                    try:
                        self.table_view.clearSelection()
                    except Exception:
                        pass
                    return False
        except Exception:
            pass
        return super().eventFilter(obj, event)