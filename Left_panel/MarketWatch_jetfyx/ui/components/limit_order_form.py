"""
Limit/Stop Order Form Component - Form for placing limit and stop orders
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.ui.components.volume_control import VolumeControl
from MarketWatch_jetfyx.ui.components.numeric_input import NumericInput
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES, SIZES
import logging

LOG = logging.getLogger(__name__)


class LimitOrderForm(QWidget):
    """Reusable limit/stop order form component"""
    
    orderSubmitted = Signal(dict)  # Emits order data
    
    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, parent=None):
        super().__init__(parent)
        
        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        
        self.setup_ui(default_lot)
    
    def setup_ui(self, default_lot):
        """Setup the form UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Top row: Volume, Contract Value, Margin
        top_row = self._create_top_row(default_lot)
        
        # Entry Price, Stop Loss, Take Profit row
        price_row = self._create_price_row()
        
        # Expiration Date & Time
        expiration_row = self._create_expiration_row()
        
        # Buy/Sell buttons
        buttons_row = self._create_buttons_row()
        
        # Remarks
        remarks_section = self._create_remarks_section()
        
        # Info row
        info_row = self._create_info_row()
        
        # Add all to layout
        layout.addLayout(top_row)
        layout.addLayout(price_row)
        layout.addLayout(expiration_row)
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
        margin_container = self._create_info_field("Margin", "≈ 11.68880")
        
        row.addWidget(self.volume_control)
        row.addLayout(contract_value_container)
        row.addLayout(margin_container)
        
        return row
    
    def _create_price_row(self):
        """Create Entry Price, Stop Loss, Take Profit row"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Stop Loss
        self.stop_loss_input = NumericInput(
            label_text="",
            placeholder="Stop Loss",
            default_value=0.0,
            decimals=5
        )
        
        # Entry Price
        self.entry_price_input = NumericInput(
            label_text="",
            placeholder="Entry Price",
            default_value=float(self.sell_price) if self.sell_price else 0.0,
            decimals=5
        )
        self.entry_price_input.set_value(float(self.sell_price) if self.sell_price else 0.0)
        
        # Take Profit
        self.take_profit_input = NumericInput(
            label_text="",
            placeholder="Take Profit",
            default_value=0.0,
            decimals=5
        )
        
        row.addWidget(self.stop_loss_input)
        row.addWidget(self.entry_price_input)
        row.addWidget(self.take_profit_input)
        
        return row
    
    def _create_expiration_row(self):
        """Create Expiration Date & Time row"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Label
        label = QLabel("Expiration Date & Time")
        label.setStyleSheet("font-size: 13px; color: #666;")
        
        # Checkbox
        self.expiration_checkbox = QCheckBox()
        self.expiration_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ddd;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background: #1976d2;
                border-color: #1976d2;
            }
        """)
        
        row.addStretch()
        row.addWidget(label)
        row.addWidget(self.expiration_checkbox)
        row.addStretch()
        
        return row
    
    def _create_buttons_row(self):
        """Create Sell Limit / Buy Stop buttons"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Sell Limit button
        self.sell_limit_btn = QPushButton(f"{self.sell_price}\nSell Limit")
        self.sell_limit_btn.setFixedHeight(80)
        self.sell_limit_btn.setStyleSheet(BUTTON_STYLES['sell'])
        self.sell_limit_btn.clicked.connect(lambda: self._submit_order("SELL_LIMIT"))
        
        # Buy Stop button
        self.buy_stop_btn = QPushButton(f"{self.buy_price}\nBuy Stop")
        self.buy_stop_btn.setFixedHeight(80)
        self.buy_stop_btn.setStyleSheet(BUTTON_STYLES['buy'])
        self.buy_stop_btn.clicked.connect(lambda: self._submit_order("BUY_STOP"))
        
        row.addWidget(self.sell_limit_btn)
        row.addWidget(self.buy_stop_btn)
        
        return row
    
    def _create_remarks_section(self):
        """Create remarks input section"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        
        label = QLabel("Remarks")
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        self.remarks_input.setFixedHeight(60)
        self.remarks_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background: white;
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(self.remarks_input)
        
        return container
    
    def _create_info_row(self):
        """Create bottom info row"""
        row = QHBoxLayout()
        row.setSpacing(20)
        
        info_items = [
            ("Spread", "0.00014"),
            ("Commission", "4"),
            ("Pip Value", "10"),
            ("Daily Swap USD", "Sell: -2.79  Buy: -3.15")
        ]
        
        for label_text, value_text in info_items:
            container = QVBoxLayout()
            container.setSpacing(2)
            
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #999;")
            label.setAlignment(Qt.AlignCenter)
            
            value = QLabel(value_text)
            value.setStyleSheet("font-size: 11px; color: #666; font-weight: bold;")
            value.setAlignment(Qt.AlignCenter)
            
            container.addWidget(label)
            container.addWidget(value)
            
            row.addLayout(container)
        
        return row
    
    def _create_info_field(self, label_text, value_text):
        """Create an info field (Contract Value, Margin)"""
        container = QVBoxLayout()
        container.setSpacing(5)
        
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        
        value = QLabel(value_text)
        value.setAlignment(Qt.AlignCenter)
        value.setFixedHeight(40)
        value.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                color: #333;
                padding: 5px;
            }
        """)
        
        container.addWidget(label)
        container.addWidget(value)
        
        return container
    
    def _submit_order(self, order_type):
        """Submit limit/stop order"""
        order_data = {
            'symbol': self.symbol,
            'type': order_type,
            'volume': self.volume_control.get_volume(),
            'entry_price': self.entry_price_input.get_value(),
            'stop_loss': self.stop_loss_input.get_value() if self.stop_loss_input.get_text() else None,
            'take_profit': self.take_profit_input.get_value() if self.take_profit_input.get_text() else None,
            'remarks': self.remarks_input.toPlainText(),
            'has_expiration': self.expiration_checkbox.isChecked(),
            'order_category': 'limit'
        }
        LOG.info("LimitOrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)
    
    def update_prices(self, sell_price, buy_price):
        """Update displayed prices"""
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.sell_limit_btn.setText(f"{sell_price}\nSell Limit")
        self.buy_stop_btn.setText(f"{buy_price}\nBuy Stop")
        self.entry_price_input.set_value(float(sell_price) if sell_price else 0.0)
        LOG.debug("LimitOrderForm update_prices: %s %s", sell_price, buy_price)
