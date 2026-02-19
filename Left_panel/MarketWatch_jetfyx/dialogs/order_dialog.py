from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.ui.components.market_order_form import MarketOrderForm
from MarketWatch_jetfyx.ui.components.limit_order_form import LimitOrderForm
from MarketWatch_jetfyx.config.ui_config import SIZES


class OrderDialog(QDialog):
    """Dialog for placing orders - uses modular form components"""
    
    orderPlaced = Signal(str, str, float)  # order_type, symbol, volume
    
    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, symbol_manager=None, order_service=None, parent=None):
        super().__init__(parent)
        
        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.symbol_manager = symbol_manager
        self.order_service = order_service
        
        self.setWindowTitle("New Order")
        self.setModal(True)
        self.setFixedSize(SIZES['dialog_width'], SIZES['dialog_height'])
        
        self.setup_ui(default_lot)
        # Connect to live price updates if a symbol manager was provided
        self._price_conn = False
        if self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.connect(self._on_price_update)
                self._price_conn = True
            except Exception:
                self._price_conn = False
    
    def setup_ui(self, default_lot):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = self._create_header()
        
        # Subtitle
        subtitle = QLabel("Majors -Euro vs US Dollar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
                color: #666;
                background: transparent;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:selected {
                border-bottom: 3px solid #1976d2;
                color: #1976d2;
            }
        """)
        
        # Market Order Tab with form component
        self.market_form = MarketOrderForm(self.symbol, self.sell_price, self.buy_price, default_lot, self)
        self.market_form.orderSubmitted.connect(self.handle_market_order)
        
        # Limit/Stop Order Tab with form component
        self.limit_form = LimitOrderForm(self.symbol, self.sell_price, self.buy_price, default_lot, self)
        self.limit_form.orderSubmitted.connect(self.handle_limit_order)
        
        tabs.addTab(self.market_form, "Market Order")
        tabs.addTab(self.limit_form, "Limit / Stop Order")
        
        layout.addLayout(header)
        layout.addWidget(subtitle)
        layout.addWidget(tabs)
    
    def _create_header(self):
        """Create dialog header"""
        header = QHBoxLayout()
        header.addStretch()
        
        # Symbol with dropdown and info
        symbol_container = QHBoxLayout()
        symbol_container.setSpacing(8)
        
        self.symbol_label = QLabel(self.symbol)
        self.symbol_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        
        symbol_dropdown = QPushButton("▼")
        symbol_dropdown.setFixedSize(30, 30)
        symbol_dropdown.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                color: #666;
            }
            QPushButton:hover {
                background: #f5f5f5;
                border-color: #1976d2;
                color: #1976d2;
            }
        """)
        symbol_dropdown.clicked.connect(self.open_symbol_search)
        
        info_btn = QPushButton("ⓘ")
        info_btn.setFixedSize(30, 30)
        info_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 16px;
                color: #1976d2;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)
        
        symbol_container.addWidget(self.symbol_label)
        symbol_container.addWidget(symbol_dropdown)
        symbol_container.addWidget(info_btn)
        
        header.addLayout(symbol_container)
        header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                color: #666;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        header.addWidget(close_btn)
        
        return header
    
    def open_symbol_search(self):
        """Open symbol search dialog"""
        from MarketWatch_jetfyx.dialogs.symbol_search_dialog import SymbolSearchDialog
        
        if not self.symbol_manager:
            return
        
        dialog = SymbolSearchDialog(self.symbol_manager, self)
        dialog.symbolSelected.connect(self.change_symbol)
        dialog.exec()
    
    def change_symbol(self, symbol_name, sell_price, buy_price):
        """Change the current symbol"""
        self.symbol = symbol_name
        self.sell_price = sell_price
        self.buy_price = buy_price
        
        self.symbol_label.setText(symbol_name)
        self.market_form.update_prices(sell_price, buy_price)
        self.limit_form.update_prices(sell_price, buy_price)

    def _on_price_update(self, symbol_name, sell, buy):
        """Handle live price updates from SymbolManager and update forms."""
        if symbol_name != self.symbol:
            return
        try:
            self.market_form.update_prices(sell, buy)
            self.limit_form.update_prices(sell, buy)
            # Also update header prices if needed
            self.sell_price = sell
            self.buy_price = buy
        except Exception:
            pass

    def accept(self):
        # Disconnect price signal to avoid callbacks after dialog is closed
        if getattr(self, '_price_conn', False) and self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.disconnect(self._on_price_update)
            except Exception:
                pass
            self._price_conn = False
        return super().accept()

    def reject(self):
        # Ensure disconnect on cancel
        if getattr(self, '_price_conn', False) and self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.disconnect(self._on_price_update)
            except Exception:
                pass
            self._price_conn = False
        return super().reject()
    
    def handle_market_order(self, order_data):
        """Handle market order submission"""
        if self.order_service:
            self.order_service.place_market_order(
                order_data['symbol'],
                order_data['type'],
                order_data['volume'],
                order_data.get('stop_loss'),
                order_data.get('take_profit'),
                order_data.get('remarks', '')
            )
        else:
            print(f"Market {order_data['type']} - Symbol: {order_data['symbol']}, Volume: {order_data['volume']}")
        
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()
    
    def handle_limit_order(self, order_data):
        """Handle limit/stop order submission"""
        if self.order_service:
            self.order_service.place_limit_order(
                order_data['symbol'],
                order_data['type'],
                order_data['volume'],
                order_data.get('entry_price'),
                order_data.get('stop_loss'),
                order_data.get('take_profit')
            )
        else:
            print(f"Limit {order_data['type']} - Symbol: {order_data['symbol']}, Volume: {order_data['volume']}, Entry: {order_data.get('entry_price')}")
        
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()
