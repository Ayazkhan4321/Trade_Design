from PySide6.QtWidgets import QTableView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Signal
from PySide6.QtCore import QRect
from MarketWatch_jetfyx.models.market_model import MarketModel
from MarketWatch_jetfyx.ui.trade_panel import TradePanel
from MarketWatch_jetfyx.ui.row_hover_delegate import RowHoverDelegate
from MarketWatch_jetfyx.ui.advance_view_delegate import AdvanceViewDelegate


class MarketTable(QTableView):
    """Table view for displaying market symbols with expandable trade panels"""

    favoriteToggled = Signal(str, bool)  # symbol_name, is_favorite

    # --------------------------------------------------
    # 🔄 PARTIAL UPDATE (NO REBUILD)
    # --------------------------------------------------
    def update_symbols(self, symbols: set):
        """Update only affected rows and update TradePanel if expanded row is affected. Logs latency if timestamp is present."""
        if not symbols:
            return

        # Safety check: ensure model still exists (may have been deleted if widget was destroyed)
        if not self.model or not hasattr(self.model, 'rows'):
            return

        import time
        try:
            for row, row_data in enumerate(self.model.rows):
                if not isinstance(row_data, dict):
                    continue  # skip invalid/category rows

                symbol = row_data.get("symbol")
                if symbol in symbols:
                    # Safety check before accessing model methods
                    if not self.model or not hasattr(self.model, 'columnCount'):
                        return
                    
                    self.model.dataChanged.emit(
                        self.model.index(row, 0),
                        self.model.index(row, self.model.columnCount() - 1)
                    )
                    # If this is the expanded row, update the TradePanel
                    if self.expanded_row == row:
                        panel = self.indexWidget(self.model.index(row, 0))
                        if isinstance(panel, TradePanel):
                            # Get latest prices from row_data
                            sell = row_data.get("sell", "")
                            buy = row_data.get("buy", "")
                            # Pass timestamp for latency logging in TradePanel
                            panel.update_prices(sell, buy, hub_received_timestamp=row_data.get('hub_received_timestamp'))
        except RuntimeError:
            # Model was deleted while we were updating - this is safe to ignore
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

        # Slightly increase default row height for readability
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
        # Prevent inline editing on single click; open TradePanel instead
        try:
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        except Exception:
            pass
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.setAlternatingRowColors(True)

        # Make all columns stretch equally
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # SYMBOL
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # SELL
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # BUY
        
        self.clicked.connect(self.toggle_row)

    # --------------------------------------------------
    # VIEW MODE
    # --------------------------------------------------
    def set_advance_view(self, enabled: bool):
        if self.expanded_row is not None:
            self.close_expanded_panel()

        self.model.set_advance_view(enabled)
        self.setItemDelegate(self.advance_delegate if enabled else self.normal_delegate)

        # Use slightly larger sizes than before
        self.verticalHeader().setDefaultSectionSize(48 if enabled else 30)
        
        # Configure column resize modes - all columns stretch equally
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # SYMBOL
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # SELL
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # BUY
        
        if enabled:
            # Advance view with TIME column
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # TIME

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

    def toggle_row(self, index):
        row = index.row()

        if row == self.expanded_row:
            return

        row_data = self.model.rows[row]
        if not isinstance(row_data, dict):
            return

        self.close_expanded_panel()

        symbol = row_data.get("symbol", "")
        sell = row_data.get("sell", "")
        buy = row_data.get("buy", "")

        self.original_row_data = row_data.copy()

        panel = TradePanel(
            symbol,
            sell,
            buy,
            self.symbol_manager,
            self.app_settings,
            self.order_service
        )

        panel.closeRequested.connect(self.collapse_row)
        panel.favoriteToggled.connect(
            lambda name, status: self.favoriteToggled.emit(name, status)
        )

        # Hide underlying row text (KEEP DICT)
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
        self.clearSelection()

        # Ensure focus stays on the table (prevent newly inserted widgets from stealing focus)
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
        index = self.indexAt(event.position().toPoint())
        row = index.row() if index.isValid() else -1

        if row != self.hovered_row:
            self.hovered_row = row
            self.viewport().update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        # Detect clicks on the hover-star area and toggle favorite
        try:
            pos = event.position().toPoint()
        except Exception:
            pos = event.pos()

        index = self.indexAt(pos)
        row = index.row() if index.isValid() else -1

        if row >= 0 and row == self.hovered_row:
            symbol = self.get_symbol_at_row(row)
            if symbol:
                # Compute visual rect for the row (column 0)
                rect = self.visualRect(self.model.index(row, 0))
                # Star area: 20px square placed 24px from right
                star_w = 20
                star_h = 20
                star_x = rect.right() - 24
                star_y = rect.top() + (rect.height() - star_h) // 2
                star_rect = QRect(star_x, star_y, star_w, star_h)

                if star_rect.contains(pos):
                    # Toggle via symbol_manager if available
                    try:
                        if getattr(self, 'symbol_manager', None):
                            # Toggle favorite state
                            self.symbol_manager.toggle_favorite(symbol)
                            is_fav = self.symbol_manager.is_favorite(symbol)
                            # Emit signal so MarketWidget can sync backend
                            self.favoriteToggled.emit(symbol, is_fav)
                            # Request repaint
                            self.viewport().update()
                            return
                    except Exception:
                        pass

        # If click is on a valid symbol cell (not the star), select the entire row
        # and open the trade panel immediately without letting the view attempt
        # to start an inline editor. This avoids showing a brief editable caret
        # in the clicked cell. The favorites table uses this behavior.
        try:
            if row >= 0 and index.isValid():
                # Select full row
                try:
                    self.selectRow(row)
                except Exception:
                    pass

                # Open trade panel for this row (mimic clicked behavior)
                try:
                    self.toggle_row(index)
                except Exception:
                    pass

                # Do not call base implementation to prevent default edit/start
                return
        except Exception:
            pass

        return super().mousePressEvent(event)

    def leaveEvent(self, event):
        self.hovered_row = -1
        self.viewport().update()
        super().leaveEvent(event)
