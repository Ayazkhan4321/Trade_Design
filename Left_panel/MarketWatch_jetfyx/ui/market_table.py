from PySide6.QtWidgets import QTableView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Signal
from PySide6.QtCore import QRect, Qt
from MarketWatch_jetfyx.models.market_model import MarketModel
from MarketWatch_jetfyx.ui.trade_panel import TradePanel
from MarketWatch_jetfyx.ui.row_hover_delegate import RowHoverDelegate
from MarketWatch_jetfyx.ui.advance_view_delegate import AdvanceViewDelegate
from MarketWatch_jetfyx.ui.symbol_context_menu import SymbolContextMenu   # ← NEW


class MarketTable(QTableView):
    """Table view for displaying market symbols with expandable trade panels"""

    favoriteToggled = Signal(str, bool)
    symbolSelected = Signal(str)  # symbol_name, is_favorite

    # --------------------------------------------------
    # 🔄 PARTIAL UPDATE (NO REBUILD)
    # --------------------------------------------------
    def update_symbols(self, symbols: set):
        """Update only affected rows and update TradePanel if expanded row is affected."""
        if not symbols:
            return

        if not self.model or not hasattr(self.model, 'rows'):
            return

        try:
            for row, row_data in enumerate(self.model.rows):
                if not isinstance(row_data, dict):
                    continue

                symbol = row_data.get("symbol")
                if symbol in symbols:
                    if not self.model or not hasattr(self.model, 'columnCount'):
                        return

                    self.model.dataChanged.emit(
                        self.model.index(row, 0),
                        self.model.index(row, self.model.columnCount() - 1)
                    )
                    if self.expanded_row == row:
                        panel = self.indexWidget(self.model.index(row, 0))
                        if isinstance(panel, TradePanel):
                            sell = row_data.get("sell", "")
                            buy = row_data.get("buy", "")
                            panel.update_prices(sell, buy, hub_received_timestamp=row_data.get('hub_received_timestamp'))
        except RuntimeError:
            pass

    # --------------------------------------------------
    # INIT
    # --------------------------------------------------
    def __init__(self, symbol_manager=None, app_settings=None, order_service=None):
        super().__init__()

        self.symbol_manager = symbol_manager
        self.app_settings = app_settings or {}
        self.order_service = order_service

        self.setMouseTracking(True)
        self.hovered_row = -1

        try:
            self.verticalHeader().setDefaultSectionSize(30)
        except Exception:
            pass

        # Delegates
        self.normal_delegate = RowHoverDelegate(self)
        self.advance_delegate = AdvanceViewDelegate(self)
        self.setItemDelegate(self.normal_delegate)

        # Model
        self.model = MarketModel()
        self.setModel(self.model)

        # Expanded row state
        self.expanded_row = None
        self.original_row_data = None

        # View config
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        try:
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        except Exception:
            pass
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.setAlternatingRowColors(True)

        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)             # ← NEW
        self.customContextMenuRequested.connect(self._show_context_menu)  # ← NEW

        # Column resize
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.clicked.connect(self.toggle_row)

    # --------------------------------------------------
    # ★  RIGHT-CLICK CONTEXT MENU  (NEW)
    # --------------------------------------------------
    def _show_context_menu(self, local_pos):
        """Spawn SymbolContextMenu at the right-clicked symbol row."""
        index = self.indexAt(local_pos)
        if not index.isValid():
            return

        row = index.row()
        row_data = self.model.rows[row] if 0 <= row < len(self.model.rows) else None
        if not isinstance(row_data, dict):
            return                          # category / separator row – skip

        symbol = row_data.get("symbol", "")
        if not symbol:
            return

        is_fav = False
        if self.symbol_manager:
            try:
                is_fav = self.symbol_manager.is_favorite(symbol)
            except Exception:
                pass

        # ── Blur the ENTIRE main window while the menu is open ──────────
        from PySide6.QtWidgets import QGraphicsBlurEffect
        blur_target = None
        try:
            # Walk up to the true top-level QMainWindow
            top = self.window()
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(8)
            blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
            top.setGraphicsEffect(blur_effect)
            blur_target = top
        except Exception:
            pass

        SymbolContextMenu.show_for_symbol(
            symbol      = symbol,
            is_favorite = is_fav,
            global_pos  = self.viewport().mapToGlobal(local_pos),
            parent      = self,
            on_new_order   = self._ctx_new_order,
            on_show_chart  = self._ctx_show_chart,
            on_symbol_info = self._ctx_symbol_info,
            on_refresh     = self._ctx_refresh_price,
            on_favorite    = self._ctx_toggle_favorite,
        )

        # ── Remove blur after menu closes ────────────────────────────
        try:
            if blur_target is not None:
                blur_target.setGraphicsEffect(None)
        except Exception:
            pass

    # -- handlers called by the menu ----------------------------------------

    def _ctx_new_order(self, symbol: str):
        """Open a New Order dialog / trade panel for *symbol*."""
        # Find the row for this symbol and expand it (re-use existing logic)
        for row, row_data in enumerate(self.model.rows):
            if isinstance(row_data, dict) and row_data.get("symbol") == symbol:
                self.toggle_row(self.model.index(row, 0))
                break

    def _ctx_show_chart(self, symbol: str):
        """Emit symbolSelected so the parent window can switch the chart."""
        self.symbolSelected.emit(symbol)

    def _ctx_symbol_info(self, symbol: str):
        """Override / connect in a subclass to show a symbol-info dialog."""
        pass  # hook – connect externally if needed

    def _ctx_refresh_price(self, symbol: str):
        """Force a UI refresh for this symbol's row."""
        for row, row_data in enumerate(self.model.rows):
            if isinstance(row_data, dict) and row_data.get("symbol") == symbol:
                self.model.dataChanged.emit(
                    self.model.index(row, 0),
                    self.model.index(row, self.model.columnCount() - 1)
                )
                break

    def _ctx_toggle_favorite(self, symbol: str, new_state: bool):
        """Toggle favourite from the context menu."""
        try:
            if self.symbol_manager:
                self.symbol_manager.toggle_favorite(symbol)
                is_fav = self.symbol_manager.is_favorite(symbol)
                self.favoriteToggled.emit(symbol, is_fav)
                self.viewport().update()
        except Exception:
            pass

    # --------------------------------------------------
    # VIEW MODE
    # --------------------------------------------------
    def set_advance_view(self, enabled: bool):
        if self.expanded_row is not None:
            self.close_expanded_panel()

        self.model.set_advance_view(enabled)
        self.setItemDelegate(self.advance_delegate if enabled else self.normal_delegate)
        self.verticalHeader().setDefaultSectionSize(48 if enabled else 30)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        if enabled:
            header.setSectionResizeMode(3, QHeaderView.Stretch)

    # --------------------------------------------------
    # DATA
    # --------------------------------------------------
    def set_symbols(self, symbols):
        self.close_expanded_panel()
        self.model.set_rows(symbols)

    def get_symbol_at_row(self, row):
        if 0 <= row < len(self.model.rows):
            row_data = self.model.rows[row]
            if isinstance(row_data, dict):
                return row_data.get("symbol")
        return None

    # --------------------------------------------------
    # EXPAND / COLLAPSE
    # --------------------------------------------------
    def close_expanded_panel(self):
        if self.expanded_row is None:
            return

        self.hovered_row = -1
        self.clearSpans()
        self.setIndexWidget(self.model.index(self.expanded_row, 0), None)

        self.model.rows[self.expanded_row] = self.original_row_data
        self.model.dataChanged.emit(
            self.model.index(self.expanded_row, 0),
            self.model.index(self.expanded_row, self.model.columnCount() - 1)
        )

        self.setRowHeight(self.expanded_row, self.verticalHeader().defaultSectionSize())
        self.expanded_row = None
        self.original_row_data = None
        self.clearSelection()
        self.setCurrentIndex(self.model.index(-1, -1))
        self.viewport().update()

    def toggle_row(self, index):
        row = index.row()

        if row == self.expanded_row:
            return

        row_data = self.model.rows[row]
        if not isinstance(row_data, dict):
            return

        self.close_expanded_panel()
        self.hovered_row = -1

        symbol = row_data.get("symbol", "")
        sell   = row_data.get("sell", "")
        buy    = row_data.get("buy", "")

        self.symbolSelected.emit(symbol)
        self.original_row_data = row_data.copy()

        panel = TradePanel(
            symbol, sell, buy,
            self.symbol_manager,
            self.app_settings,
            self.order_service
        )
        panel.closeRequested.connect(self.collapse_row)
        panel.favoriteToggled.connect(
            lambda name, status: self.favoriteToggled.emit(name, status)
        )

        hidden_row = row_data.copy()
        for key in hidden_row:
            hidden_row[key] = ""

        self.model.rows[row] = hidden_row
        self.model.dataChanged.emit(
            self.model.index(row, 0),
            self.model.index(row, self.model.columnCount() - 1)
        )

        column_count = self.model.columnCount()
        self.setSpan(row, 0, 1, column_count)
        self.setIndexWidget(self.model.index(row, 0), panel)
        self.setRowHeight(row, 100)
        self.expanded_row = row
        self.viewport().update()
        self.clearSelection()

        try:
            self.setFocus()
        except Exception:
            pass

    def collapse_row(self):
        self.close_expanded_panel()

    # --------------------------------------------------
    # HOVER
    # --------------------------------------------------
    def mouseMoveEvent(self, event):
        # While a trade panel is open, suppress hover tracking entirely so
        # hovered_row never goes stale and bleeds through on close.
        if self.expanded_row is not None:
            if self.hovered_row != -1:
                self.hovered_row = -1
                self.viewport().update()
            return super().mouseMoveEvent(event)

        index = self.indexAt(event.position().toPoint())
        row = index.row() if index.isValid() else -1

        if row != self.hovered_row:
            self.hovered_row = row
            self.viewport().update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        # Right-click: open context menu directly WITHOUT calling super() so Qt
        # never selects/highlights the row at all.
        if event.button() == Qt.RightButton:
            try:
                local_pos = event.position().toPoint()
            except Exception:
                local_pos = event.pos()
            self._show_context_menu(local_pos)
            return

        try:
            pos = event.position().toPoint()
        except Exception:
            pos = event.pos()

        index = self.indexAt(pos)
        row = index.row() if index.isValid() else -1

        if row >= 0 and row == self.hovered_row:
            symbol = self.get_symbol_at_row(row)
            if symbol:
                last_col = self.model.columnCount() - 1
                rect = self.visualRect(self.model.index(row, last_col))
                if rect.contains(pos):
                    try:
                        if getattr(self, 'symbol_manager', None):
                            self.symbol_manager.toggle_favorite(symbol)
                            is_fav = self.symbol_manager.is_favorite(symbol)
                            self.favoriteToggled.emit(symbol, is_fav)
                            self.viewport().update()
                            return
                    except Exception:
                        pass

        try:
            if row >= 0 and index.isValid():
                try:
                    self.toggle_row(index)
                except Exception:
                    pass
                return
        except Exception:
            pass

        return super().mousePressEvent(event)

    def leaveEvent(self, event):
        self.hovered_row = -1
        self.viewport().update()
        super().leaveEvent(event)