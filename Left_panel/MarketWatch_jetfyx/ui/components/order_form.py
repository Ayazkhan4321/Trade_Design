"""
Order Form Component - Reusable order form widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDoubleSpinBox, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES, SIZES
import logging

LOG = logging.getLogger(__name__)


class OrderForm(QWidget):
    """Reusable order form component"""
    
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
        
        # Volume row
        volume_row = self._create_volume_row(default_lot)
        
        # Stop Loss / Take Profit row
        sl_tp_row = self._create_sl_tp_row()
        
        # Buy/Sell buttons
        buttons_row = self._create_buttons_row()
        
        # Remarks
        remarks_section = self._create_remarks_section()
        
        # Info row
        info_row = self._create_info_row()
        
        layout.addLayout(volume_row)
        layout.addLayout(sl_tp_row)
        layout.addLayout(buttons_row)
        layout.addWidget(remarks_section)
        layout.addLayout(info_row)
    
    def _create_volume_row(self, default_lot):
        """Create volume input row"""
        row = QHBoxLayout()
        
        # Volume control
        vol_container = QVBoxLayout()
        vol_label = QLabel("Volume")
        vol_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        
        vol_control = QHBoxLayout()
        vol_down = QPushButton("▼")
        vol_down.setFixedSize(*SIZES['button_medium'])
        vol_down.setStyleSheet(BUTTON_STYLES['standard'])
        
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setDecimals(2)
        self.volume_input.setMinimum(0.01)
        self.volume_input.setMaximum(100.0)
        self.volume_input.setSingleStep(0.01)
        self.volume_input.setValue(default_lot)
        self.volume_input.setAlignment(Qt.AlignCenter)
        self.volume_input.setFixedHeight(SIZES['input_height'])
        
        vol_up = QPushButton("▲")
        vol_up.setFixedSize(*SIZES['button_medium'])
        vol_up.setStyleSheet(BUTTON_STYLES['standard'])
        
        vol_down.clicked.connect(lambda: self.volume_input.setValue(max(0.01, self.volume_input.value() - 0.01)))
        vol_up.clicked.connect(lambda: self.volume_input.setValue(min(100.0, self.volume_input.value() + 0.01)))
        
        vol_control.addWidget(vol_down)
        vol_control.addWidget(self.volume_input)
        vol_control.addWidget(vol_up)
        
        vol_container.addWidget(vol_label)
        vol_container.addLayout(vol_control)
        
        row.addLayout(vol_container)
        
        return row
    
    def _create_sl_tp_row(self):
        """Create Stop Loss and Take Profit row"""
        row = QHBoxLayout()
        
        self.sl_input = QLineEdit("Stop Loss")
        self.sl_input.setAlignment(Qt.AlignCenter)
        self.sl_input.setFixedHeight(SIZES['input_height'])
        
        self.tp_input = QLineEdit("Take Profit")
        self.tp_input.setAlignment(Qt.AlignCenter)
        self.tp_input.setFixedHeight(SIZES['input_height'])
        
        row.addWidget(self.sl_input)
        row.addWidget(self.tp_input)
        
        return row
    
    def _create_buttons_row(self):
        """Create Buy/Sell buttons"""
        row = QHBoxLayout()
        
        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        self.sell_btn.setFixedHeight(80)
        self.sell_btn.setStyleSheet(BUTTON_STYLES['sell'])
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))
        
        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        self.buy_btn.setFixedHeight(80)
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
        
        label = QLabel("Remarks")
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        self.remarks_input.setFixedHeight(60)
        
        layout.addWidget(label)
        layout.addWidget(self.remarks_input)
        
        return container
    
    def _create_info_row(self):
        """Create info labels row"""
        row = QHBoxLayout()
        
        info_labels = [
            ("Spread", "0.00"),
            ("Commission", "0"),
            ("Pip Value", "1"),
            ("Daily Swap USD", "Sell:  Buy:")
        ]
        
        for label_text, value_text in info_labels:
            container = QVBoxLayout()
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
    
    def _submit_order(self, order_type):
        """Submit order"""
        order_data = {
            'symbol': self.symbol,
            'type': order_type,
            'volume': self.volume_input.value(),
            'stop_loss': self.sl_input.text() if self.sl_input.text() != "Stop Loss" else None,
            'take_profit': self.tp_input.text() if self.tp_input.text() != "Take Profit" else None,
            'remarks': self.remarks_input.toPlainText()
        }
        LOG.info("OrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)
    
    def update_prices(self, sell_price, buy_price, hub_received_timestamp=None):
        """Update displayed prices. Log latency if timestamp is provided."""
        import time
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.sell_btn.setText(f"{sell_price}\nSell")
        self.buy_btn.setText(f"{buy_price}\nBuy")
        if hub_received_timestamp:
            latency = (time.time() - hub_received_timestamp) * 1000  # ms
            LOG.debug("[Latency] OrderForm Buttons: %s latency = %.2f ms", self.symbol, latency)
