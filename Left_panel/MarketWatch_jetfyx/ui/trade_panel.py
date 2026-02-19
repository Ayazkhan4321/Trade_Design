from MarketWatch_jetfyx.widgets.lot_preset_widget import LotPresetWidget
from PySide6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout,QSizePolicy,
    QLabel, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging

LOG = logging.getLogger(__name__)


class TradePanel(QWidget):
    closeRequested = Signal()
    favoriteToggled = Signal(str, bool)  # symbol_name, is_favorite

    def __init__(self, symbol, sell_price, buy_price, symbol_manager=None, app_settings=None, order_service=None):
        super().__init__()

        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.symbol_manager = symbol_manager
        self.app_settings = app_settings or {}
        self.order_service = order_service
        self.current_lot = self.app_settings.get('default_lot', 0.01) if self.app_settings.get('default_lot_enabled', False) else 0.01
        
        # Set initial favorite state from symbol manager
        self.is_favorite = symbol_manager.is_favorite(symbol) if symbol_manager else False
       

        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with symbol and action buttons
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(6, 3, 6, 3)
        top_bar.setSpacing(4)

        # Symbol label
        symbol_label = QLabel(f"{symbol} ({sell_price})")
        symbol_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        # Top action buttons
        self.btn_favorite = QPushButton("★" if self.is_favorite else "☆")
        self.btn_favorite.setFixedSize(22, 22)
        self._update_favorite_style()
        self.btn_favorite.clicked.connect(self.toggle_favorite)

        btn_place_order = QPushButton("+")
        btn_place_order.setFixedSize(22, 22)
        btn_place_order.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        btn_place_order.clicked.connect(self.place_order)

        btn_info = QPushButton("ⓘ")
        btn_info.setFixedSize(22, 22)
        btn_info.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1976d2;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(22, 22)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)
        btn_close.clicked.connect(self.closeRequested.emit)

        top_bar.addWidget(symbol_label)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_favorite)
        top_bar.addWidget(btn_place_order)
        top_bar.addWidget(btn_info)
        top_bar.addWidget(btn_close)

        # Main trading panel
        trade_layout = QHBoxLayout()
        trade_layout.setContentsMargins(8, 6, 8, 6)
        trade_layout.setSpacing(10)

        # SELL Button with L label
        sell_box = QVBoxLayout()
        sell_box.setSpacing(2)
        sell_box.setAlignment(Qt.AlignCenter)

        self.sell_btn = QPushButton(f"SELL\n{sell_price}")
        self.sell_btn.setMinimumWidth(90)
        self.sell_btn.setMinimumHeight(45)
        self.sell_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sell_btn.setStyleSheet("""
            QPushButton {
                background: #e53935;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #c62828;
            }
        """)
        self.sell_btn.clicked.connect(self.on_sell_clicked)

        lower_label = QLabel("L - 1.16996")
        lower_label.setAlignment(Qt.AlignCenter)
        lower_label.setStyleSheet("color: #999; font-size: 9px;")

        sell_box.addWidget(self.sell_btn)
        sell_box.addWidget(lower_label)

        # LOT COLUMN
        lot_box = QVBoxLayout()
        lot_box.setAlignment(Qt.AlignCenter)
        lot_box.setSpacing(4)

        lot_label = QLabel("LOT")
        lot_label.setAlignment(Qt.AlignCenter)
        lot_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-weight: bold;
                font-size: 10px;
            }
        """)

        # Lot control with +/- buttons
        lot_control = QHBoxLayout()
        lot_control.setSpacing(3)

        self.btn_minus = QPushButton("−")
        self.btn_minus.setFixedSize(18, 21)
        self.btn_minus.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.btn_minus.clicked.connect(self.decrease_lot)

        self.lot_display = QLineEdit()
        self.lot_display.setText(f"{self.current_lot:.2f}")
        self.lot_display.setAlignment(Qt.AlignCenter)
        self.lot_display.setFixedSize(46, 21)
        self.lot_display.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #1976d2;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
        """)
        self.lot_display.textChanged.connect(self.on_lot_text_changed)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(18, 21)
        self.btn_plus.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.btn_plus.clicked.connect(self.increase_lot)

        lot_control.addWidget(self.btn_minus)
        lot_control.addWidget(self.lot_display)
        lot_control.addWidget(self.btn_plus)

        # LOT PRESETS
        self.lot_widget = LotPresetWidget()

        #lot_box.addWidget(lot_label)
        lot_box.addLayout(lot_control)
        lot_box.addWidget(self.lot_widget)

        # BUY Button with H label
        buy_box = QVBoxLayout()
        buy_box.setSpacing(2)
        buy_box.setAlignment(Qt.AlignCenter)


        self.buy_btn = QPushButton(f"BUY\n{buy_price}")
        self.buy_btn.setMinimumWidth(90)
        self.buy_btn.setMinimumHeight(45)
        self.buy_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background: #2e7d32;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #1b5e20;
            }
        """)
        self.buy_btn.clicked.connect(self.on_buy_clicked)

        higher_label = QLabel("H - 1.17430")
        higher_label.setAlignment(Qt.AlignCenter)
        higher_label.setStyleSheet("color: #999; font-size: 9px;")

        buy_box.addWidget(self.buy_btn)
        buy_box.addWidget(higher_label)
        
        trade_layout = QHBoxLayout()
        trade_layout.setContentsMargins(8, 6, 8, 6)
        trade_layout.setSpacing(10)

        trade_layout.addStretch()
        trade_layout.addLayout(sell_box)
        trade_layout.addLayout(lot_box)
        trade_layout.addLayout(buy_box)
        trade_layout.addStretch()

        main_layout.addLayout(top_bar)
        main_layout.addLayout(trade_layout)

        # Set background
        self.setStyleSheet("""
            TradePanel {
                background: #e3f2fd;
                border: 2px solid #90caf9;
                border-radius: 4px;
            }
        """)

        # 🔌 Connect to live price updates
        if self.symbol_manager and hasattr(self.symbol_manager, "priceUpdated"):
            self.symbol_manager.priceUpdated.connect(self.on_price_update)

    def increase_lot(self):
        # Get the selected preset value and add it to current lot
        selected_lot = self.lot_widget.get_selected_lot()
        self.current_lot = min(100, self.current_lot + selected_lot)
        self.lot_display.setText(f"{self.current_lot:.2f}")

    def decrease_lot(self):
        # Get the selected preset value and subtract it from current lot
        selected_lot = self.lot_widget.get_selected_lot()
        self.current_lot = max(0.01, self.current_lot - selected_lot)
        self.lot_display.setText(f"{self.current_lot:.2f}")

    def on_lot_text_changed(self, text):
        try:
            value = float(text)
            if 0.01 <= value <= 100:
                self.current_lot = value
        except ValueError:
            pass

    def toggle_favorite(self):
        """Toggle favorite status and update button appearance"""
        self.is_favorite = not self.is_favorite
        
        # Update symbol manager
        if self.symbol_manager:
            self.symbol_manager.toggle_favorite(self.symbol)
        
        # Emit signal
        self.favoriteToggled.emit(self.symbol, self.is_favorite)
        
        # Update button appearance
        self.btn_favorite.setText("★" if self.is_favorite else "☆")
        self._update_favorite_style()
    
    def _update_favorite_style(self):
        """Update the favorite button style based on state"""
        if self.is_favorite:
            style = """
                QPushButton {
                    background: transparent;
                    color: #ffa500;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                }
            """
        else:
            style = """
                QPushButton {
                    background: transparent;
                    color: #ccc;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                }
            """
        self.btn_favorite.setStyleSheet(style)

    def on_sell_clicked(self):
        """Handle SELL button click"""
        one_click_trade = self.app_settings.get('one_click_trade', False)
        LOG.info("SELL clicked: symbol=%s lot=%s one_click=%s", self.symbol, self.current_lot, one_click_trade)
        if one_click_trade:
            # Execute immediately using order service
            if self.order_service:
                result = self.order_service.place_market_order(
                    self.symbol,
                    "SELL",
                    self.current_lot
                )
                if result:
                    LOG.info("SELL executed via OrderService: %s", result)
                else:
                    LOG.error("SELL execution failed for %s", self.symbol)
            else:
                LOG.info("SELL clicked (no order_service): Symbol=%s Lot=%s", self.symbol, self.current_lot)
        else:
            # Open order dialog
            self.open_order_dialog("SELL")
    
    def on_buy_clicked(self):
        """Handle BUY button click"""
        one_click_trade = self.app_settings.get('one_click_trade', False)
        LOG.info("BUY clicked: symbol=%s lot=%s one_click=%s", self.symbol, self.current_lot, one_click_trade)
        if one_click_trade:
            # Execute immediately using order service
            if self.order_service:
                result = self.order_service.place_market_order(
                    self.symbol,
                    "BUY",
                    self.current_lot
                )
                if result:
                    LOG.info("BUY executed via OrderService: %s", result)
                else:
                    LOG.error("BUY execution failed for %s", self.symbol)
            else:
                LOG.info("BUY clicked (no order_service): Symbol=%s Lot=%s", self.symbol, self.current_lot)
        else:
            # Open order dialog
            self.open_order_dialog("BUY")
    
    def open_order_dialog(self, order_type):
        """Open the order placement dialog"""
        from MarketWatch_jetfyx.dialogs.order_dialog import OrderDialog
        
        default_lot = self.app_settings.get('default_lot', 0.01) if self.app_settings.get('default_lot_enabled', False) else self.current_lot
        
        dialog = OrderDialog(
            self.symbol, 
            self.sell_price, 
            self.buy_price, 
            default_lot, 
            self.symbol_manager,
            self.order_service,
            self
        )
        dialog.orderPlaced.connect(lambda order_type, symbol, volume: 
            LOG.info("Dialog order placed: %s %s %s", order_type, symbol, volume))
        dialog.exec()

    def place_order(self):
        """Open place order dialog"""
        # Open order dialog with default order type (can be BUY or SELL based on current price)
        # Let's open it without pre-selecting an order type, user can choose in dialog
        from MarketWatch_jetfyx.dialogs.order_dialog import OrderDialog
        
        default_lot = self.app_settings.get('default_lot', 0.01) if self.app_settings.get('default_lot_enabled', False) else self.current_lot
        
        dialog = OrderDialog(
            self.symbol, 
            self.sell_price, 
            self.buy_price, 
            default_lot, 
            self.symbol_manager,
            self.order_service,
            self
        )
        dialog.orderPlaced.connect(lambda order_type, symbol, volume: 
            LOG.info("Dialog order placed from + button: %s %s %s", order_type, symbol, volume))
        dialog.exec()

    def update_prices(self, sell_price, buy_price, hub_received_timestamp=None):
        """Update the displayed sell and buy prices in the panel. Log latency if timestamp is provided."""
        import time
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.sell_btn.setText(f"SELL\n{sell_price}")
        self.buy_btn.setText(f"BUY\n{buy_price}")
        if hub_received_timestamp:
            latency = (time.time() - hub_received_timestamp) * 1000  # ms
            LOG.debug("[Latency] TradePanel Buttons: %s latency = %.2f ms", self.symbol, latency)

    def on_price_update(self, symbol, sell, buy):
        if symbol != self.symbol:
            return
        self.update_prices(sell, buy)