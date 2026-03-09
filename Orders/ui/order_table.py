from PySide6.QtWidgets import (
    QWidget,
    QTableView,
    QSizePolicy,
    QVBoxLayout,
    QHeaderView,
    QMenu,
    QScrollBar # 🟢 Imported explicitly
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

        # Disable hover background and enforce selection color from theme
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            self.table_view.setFocusPolicy(Qt.NoFocus)
            
            # 🟢 FIX: Use a soft light background (bg_tab_active) instead of the heavy dark block
            # And use the primary text color so it remains perfectly readable!
            light_select_bg = t.get('bg_tab_active', '#e6f0ff')
            text_color = t.get('text_primary', '#1a202c')
            
            self.table_view.setStyleSheet(
                f"QTableView::item:hover {{ background: {t.get('bg_row_hover', 'transparent')}; }}"
                f"QTableView::item:focus {{ outline: none; }}"
                f"QTableView::item:selected {{ background: {light_select_bg}; color: {text_color}; }}"
            )
            # Re-apply on theme change
            def _on_theme_changed_order_table(name, tok, tv=self.table_view):
                try:
                    l_bg = tok.get('bg_tab_active', '#e6f0ff')
                    t_col = tok.get('text_primary', '#1a202c')
                    tv.setStyleSheet(
                        f"QTableView::item:hover {{ background: {tok.get('bg_row_hover', 'transparent')}; }}"
                        f"QTableView::item:focus {{ outline: none; }}"
                        f"QTableView::item:selected {{ background: {l_bg}; color: {t_col}; }}"
                    )
                except RuntimeError:
                    # Widget was deleted, ignore
                    pass
            ThemeManager.instance().theme_changed.connect(_on_theme_changed_order_table)
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
        header = self.table_view.horizontalHeader()
        headers = self.model.headers

        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultSectionSize(95)
        header.setMinimumSectionSize(50)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(28)

        for i, col_name in enumerate(headers):
            name_upper = col_name.upper()
            if "TIME" in name_upper:
                self.table_view.setColumnWidth(i, 160)
            elif "ID" in name_upper:
                self.table_view.setColumnWidth(i, 60)
            elif name_upper in ["TYPE", "LOT SIZE", "LOT", "S/L", "T/P", "SWAP", "COMMISSION"]:
                self.table_view.setColumnWidth(i, 75)
            elif "SYMBOL" in name_upper:
                self.table_view.setColumnWidth(i, 80)
            else:
                self.table_view.setColumnWidth(i, 95)

        # -----------------------------
        # Delegates (Actions + Remarks)
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

        header.setSectionResizeMode(action_col, QHeaderView.Fixed)
        header.setSectionResizeMode(remark_col, QHeaderView.Fixed)
        self.table_view.setColumnWidth(action_col, 90)
        self.table_view.setColumnWidth(remark_col, 80)

        # -----------------------------
        # Bottom bar (column-aware)
        # -----------------------------
        self.profit_col = headers.index("PROFIT/LOSS")
        self.bottom_bar = BottomBar(self.table_view, self.profit_col)

        # -----------------------------
        # Layout: table + bottom bar + custom scrollbar
        # -----------------------------
        
        self.h_scrollbar = QScrollBar(Qt.Horizontal, self)
        
        # Brutally disable the table's native scrollbar so they don't fight
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Sync the new external scrollbar with the internal logic
        internal_bar = self.table_view.horizontalScrollBar()
        internal_bar.rangeChanged.connect(self.h_scrollbar.setRange)
        internal_bar.valueChanged.connect(self.h_scrollbar.setValue)
        self.h_scrollbar.valueChanged.connect(internal_bar.setValue)

        # Hide our custom scrollbar automatically if no scrolling is needed
        def _sync_visibility(min_val, max_val):
            self.h_scrollbar.setVisible(max_val > 0)
        internal_bar.rangeChanged.connect(_sync_visibility)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 🟢 FIX: We DO NOT use alignTop here anymore so the stretch works!

        # 🟢 FIX: The perfect stacking order with an invisible spring.
        layout.addWidget(self.table_view)     # 1. Table
        layout.addWidget(self.bottom_bar)     # 2. Bottom Bar (Slimmer now)
        layout.addStretch(1)                  # 🟢 3. The Spring: Pushes slider all the way down!
        layout.addWidget(self.h_scrollbar)    # 4. Slider rests at the absolute bottom

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # Header Click connections
        try:
            header.setSectionsClickable(True)
            def _on_header_clicked(section):
                try:
                    if section != action_col:
                        return
                    try:
                        dlg = BulkCloseDialog(self, order_service=getattr(self.model, 'order_service', None), model=self.model)
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

    # -----------------------------
    # 🟢 DYNAMIC HEIGHT CALCULATION 
    # -----------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_table_height()

    def _update_table_height(self):
        """Forces the table view height to perfectly match the number of rows, 
        snapping the bottom bar directly underneath them."""
        try:
            header_h = self.table_view.horizontalHeader().height()
            rows_h = self.table_view.verticalHeader().length()
            frame_w = self.table_view.frameWidth() * 2
            
            content_h = header_h + rows_h + frame_w
            
            if self.model.rowCount() == 0:
                content_h = header_h + frame_w
                
            # Detect height of external scrollbar if it's currently showing
            scroll_h = self.h_scrollbar.height() if self.h_scrollbar.isVisible() else 0
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