from PySide6.QtWidgets import (
    QWidget,
    QTableView,
    QSizePolicy,
    QVBoxLayout,
    QHeaderView,
    QMenu,
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QCursor, QAction
from .bulk_close_dialog import BulkCloseDialog

from ..models.order_model import OrderModel
from .bottom_bar import BottomBar

from .delegates.action_delegate import CloseDelegate
from .delegates.remark_delegate import RemarkDelegate


class OrderTable(QWidget):
    def __init__(self, order_service=None):
        super().__init__()

        # -----------------------------
        # Table view + model
        # -----------------------------
        self.table_view = QTableView(self)
        self.model = OrderModel()
        # attach service reference to model and keep locally
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

        # Track mouse moves so we can clear selection when the cursor
        # moves away from a selected row (user expectation).
        try:
            self.table_view.setMouseTracking(True)
            self.table_view.installEventFilter(self)
        except Exception:
            pass

        # Disable inline editing via the view (double-click / enter won't start editors)
        try:
            self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        except Exception:
            pass

        # Disable hover background so cells don't show a blue hover
        # (app-wide styles may enable hover; override here to make it transparent)
        try:
            # Prevent hover showing editable/focus caret; keep rows selectable.
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.setStyleSheet(
                """
                QTableView::item:hover { background: transparent; }
                QTableView::item:focus { outline: none; }
                QTableView::item:selected { background: #0b66a6; color: #fff; }
                """
            )
        except Exception:
            pass

        self.table_view.verticalHeader().setVisible(False)
        # allow scrolling when rows exceed visible area
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # let the table expand and be scrollable inside the container
        self.table_view.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # -----------------------------
        # Header configuration (🔥 FIX)
        # -----------------------------
        header = self.table_view.horizontalHeader()

        # ❌ DO NOT stretch last section
        # header.setStretchLastSection(True)  <-- REMOVED

        # Default behavior for all columns
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(80)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(28)

        # -----------------------------
        # Delegates (Actions + Remarks)
        # -----------------------------
        headers = self.model.headers

        # Robustly find the Actions and Remarks columns. The header text may
        # have been altered elsewhere (e.g. "Options ⋮"). Fall back to the
        # expected last-two-column positions if names are not found.
        def _find_index(candidates, fallback_index):
            for c in candidates:
                try:
                    return headers.index(c)
                except ValueError:
                    continue
            # fallback by index relative to end
            if fallback_index < 0:
                idx = len(headers) + fallback_index
                if 0 <= idx < len(headers):
                    return idx
            # final fallback: 0
            return 0

        action_col = _find_index(["Actions", "Options ⋮", "Options", "⋮"], -2)
        remark_col = _find_index(["Remarks", "Remark"], -1)

        # Ensure the header label remains 'Actions' while the header click
        # will present an 'Options' menu for additional actions.
        try:
            # Show three-dot affordance next to label
            self.model.headers[action_col] = "Actions  ⋮"
            try:
                header.repaint()
            except Exception:
                pass
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

        # Icon columns → fixed width
        header.setSectionResizeMode(action_col, QHeaderView.Fixed)
        header.setSectionResizeMode(remark_col, QHeaderView.Fixed)

        self.table_view.setColumnWidth(action_col, 40)
        self.table_view.setColumnWidth(remark_col, 40)

        # -----------------------------
        # Important column widths
        # -----------------------------
        def set_width(name, width):
            header.resizeSection(headers.index(name), width)

        set_width("Market Price", 120)
        set_width("Market Value", 120)
        set_width("PROFIT/LOSS", 120)
        set_width("P/L IN %", 100)
        set_width("Commission", 100)
        set_width("SWAP", 80)

        # -----------------------------
        # Bottom bar (column-aware)
        # -----------------------------
        headers = self.model.headers
        # expose profit column index for alignment
        self.profit_col = headers.index("PROFIT/LOSS")
        self.bottom_bar = BottomBar(self.table_view, self.profit_col)

        # -----------------------------
        # Layout: table + bottom bar
        # -----------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.table_view)
        layout.addWidget(self.bottom_bar)

        # let the OrderTable expand to fill available dock space (table scrolls)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        # NOTE: removed auto-resize logic so the table remains scrollable and
        # the bottom bar stays fixed. The table's scrollbar will appear as needed.

        # Make header sections clickable and handle clicks on the Options header
        try:
            header.setSectionsClickable(True)
            def _on_header_clicked(section):
                try:
                    if section != action_col:
                        return
                    # Instead of a plain menu, open the Bulk Close dialog
                    try:
                        dlg = BulkCloseDialog(self, order_service=getattr(self.model, 'order_service', None), model=self.model)
                        dlg.exec()
                    except Exception:
                        # Fallback: show a simple options menu
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

    def eventFilter(self, obj, event):
        # Handle mouse leaving the table or moving to an empty area to
        # clear any existing selection so rows don't remain selected.
        try:
            if obj is self.table_view:
                if event.type() == QEvent.Leave:
                    try:
                        self.table_view.clearSelection()
                    except Exception:
                        pass
                    return False

                if event.type() == QEvent.MouseMove:
                    # If mouse is over no valid index, clear selection
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
