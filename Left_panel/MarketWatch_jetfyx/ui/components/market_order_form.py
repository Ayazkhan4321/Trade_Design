"""
Market Order Form Component - Form for placing market orders
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.ui.components.volume_control import VolumeControl
from MarketWatch_jetfyx.ui.components.numeric_input import NumericInput
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES
import logging

LOG = logging.getLogger(__name__)


class MarketOrderForm(QWidget):
    """Reusable market order form component"""
    
    orderSubmitted = Signal(dict)  # Emits order data
    
    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, parent=None):
        super().__init__(parent)
        
        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        
        self.setup_ui(default_lot)
        self._apply_theme()
        
        # Subscribe to dynamic theme changes
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass
            
    def _apply_theme(self):
        """Apply dynamic theme colors instead of hardcoded hex values"""
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            bg_input = tok.get("bg_input", "#f5f5f5")
            text_pri = tok.get("text_primary", "#1a202c")
            text_sec = tok.get("text_secondary", "#6b7280")
            border   = tok.get("border_primary", "#e5e7eb")
            is_dark  = tok.get("is_dark", "false") == "true"
        except Exception:
            bg_input, text_pri, text_sec, border, is_dark = "#f5f5f5", "#1a202c", "#6b7280", "#e5e7eb", False

        # Force strong contrast in dark mode for better readability
        if is_dark:
            if border == "#e5e7eb": border = "#374151"
            if bg_input == "#f5f5f5": bg_input = "#1f2937"

        self.setStyleSheet(f"""
            QWidget {{ background: transparent; }}
            
            QLabel#FormLabel {{
                font-weight: bold; font-size: 12px; color: {text_sec};
            }}
            
            QLabel#FormValue, QTextEdit {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 4px;
                font-size: 13px;
                color: {text_pri};
                padding: 5px;
            }}
            
            QLabel#InfoLabel {{
                font-size: 11px; color: {text_sec};
            }}
            
            QLabel#InfoValue {{
                font-size: 11px; color: {text_pri}; font-weight: bold;
            }}
        """)
    
    def setup_ui(self, default_lot):
        """Setup the form UI"""
        layout = QVBoxLayout(self)
        # 🟢 FIX: Drastically reduced spacing and margins to remove empty space
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Volume, Contract Value, Margin row
        top_row = self._create_top_row(default_lot)
        
        # Stop Loss / Take Profit row
        sl_tp_row = self._create_sl_tp_row()
        
        # Buy/Sell buttons
        buttons_row = self._create_buttons_row()
        
        # Remarks
        remarks_section = self._create_remarks_section()
        
        # Info row
        info_row = self._create_info_row()
        
        # Add all to layout
        layout.addLayout(top_row)
        layout.addLayout(sl_tp_row)
        layout.addLayout(buttons_row)
        layout.addWidget(remarks_section)
        layout.addLayout(info_row)
    
    def _create_top_row(self, default_lot):
        """Create Volume, Contract Value, Margin row"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Volume
        self.volume_control = VolumeControl(default_lot)
        
        # Contract Value
        contract_value_container = self._create_info_field("Contract Value", "≈1000.00 USD")
        
        # Margin
        margin_container = self._create_info_field("Margin", "≈ 11.69040")
        
        row.addWidget(self.volume_control)
        row.addLayout(contract_value_container)
        row.addLayout(margin_container)
        
        return row
    
    def _create_sl_tp_row(self):
        """Create Stop Loss and Take Profit row"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Stop Loss
        self.stop_loss_input = NumericInput(
            label_text="",
            placeholder="Stop Loss",
            default_value=0.0,
            decimals=5
        )
        
        # Take Profit
        self.take_profit_input = NumericInput(
            label_text="",
            placeholder="Take Profit",
            default_value=0.0,
            decimals=5
        )
        
        row.addWidget(self.stop_loss_input)
        row.addWidget(self.take_profit_input)
        
        return row
    
    def _create_buttons_row(self):
        """Create Buy/Sell buttons"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        # 🟢 FIX: Reduced from 80 to 50 for a sleeker profile
        self.sell_btn.setFixedHeight(50)
        self.sell_btn.setStyleSheet(BUTTON_STYLES['sell'])
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))
        
        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        # 🟢 FIX: Reduced from 80 to 50
        self.buy_btn.setFixedHeight(50)
        self.buy_btn.setStyleSheet(BUTTON_STYLES['buy'])
        self.buy_btn.clicked.connect(lambda: self._submit_order("BUY"))
        
        row.addWidget(self.sell_btn)
        row.addWidget(self.buy_btn)
        
        return row
    
    def _create_remarks_section(self):
        """Create remarks input"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Remarks")
        label.setObjectName("FormLabel")
        
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        # 🟢 FIX: Reduced remarks height slightly
        self.remarks_input.setFixedHeight(45)
        
        layout.addWidget(label)
        layout.addWidget(self.remarks_input)
        
        return container
    
    def _create_info_row(self):
        """Create bottom info row"""
        row = QHBoxLayout()
        row.setSpacing(20)
        
        info_items = [
            ("Spread", "0.00019"),
            ("Commission", "4"),
            ("Pip Value", "10"),
            ("Daily Swap USD", "Sell: -2.79  Buy: -3.15")
        ]
        
        for label_text, value_text in info_items:
            container = QVBoxLayout()
            container.setSpacing(2)
            
            label = QLabel(label_text)
            label.setObjectName("InfoLabel")
            label.setAlignment(Qt.AlignCenter)
            
            value = QLabel(value_text)
            value.setObjectName("InfoValue")
            value.setAlignment(Qt.AlignCenter)
            
            container.addWidget(label)
            container.addWidget(value)
            
            row.addLayout(container)
        
        return row
    
    def _create_info_field(self, label_text, value_text):
        """Create an info field"""
        container = QVBoxLayout()
        container.setSpacing(5)
        
        label = QLabel(label_text)
        label.setObjectName("FormLabel")
        
        value = QLabel(value_text)
        value.setObjectName("FormValue")
        value.setAlignment(Qt.AlignCenter)
        # 🟢 FIX: Reduced height from 40 to 32
        value.setFixedHeight(32)
        
        container.addWidget(label)
        container.addWidget(value)
        
        return container
    
    def _submit_order(self, order_type):
        """Submit market order"""
        order_data = {
            'symbol': self.symbol,
            'type': order_type,
            'volume': self.volume_control.get_volume(),
            'stop_loss': self.stop_loss_input.get_value() if self.stop_loss_input.get_text() else None,
            'take_profit': self.take_profit_input.get_value() if self.take_profit_input.get_text() else None,
            'remarks': self.remarks_input.toPlainText(),
            'order_category': 'market'
        }
        LOG.info("MarketOrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)
    
    def update_prices(self, sell_price, buy_price):
        """Update displayed prices"""
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.sell_btn.setText(f"{sell_price}\nSell")
        self.buy_btn.setText(f"{buy_price}\nBuy")
        LOG.debug("MarketOrderForm update_prices: %s %s", sell_price, buy_price)