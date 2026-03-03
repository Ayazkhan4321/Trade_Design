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
        self._apply_theme()
        
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass
            
    def _apply_theme(self):
        """Apply dynamic theme colors and fix volume buttons UI"""
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            bg_input = tok.get("bg_input", "#f5f5f5")
            text_pri = tok.get("text_primary", "#1a202c")
            text_sec = tok.get("text_secondary", "#6b7280")
            border   = tok.get("border_primary", "#e5e7eb")
            bg_hover = tok.get("bg_button_hover", "#e2e8f0")
            is_dark  = tok.get("is_dark", "false") == "true"
        except Exception:
            bg_input, text_pri, text_sec, border, bg_hover, is_dark = "#f5f5f5", "#1a202c", "#6b7280", "#e5e7eb", "#e2e8f0", False

        if is_dark:
            if border == "#e5e7eb": border = "#374151"
            if bg_input == "#f5f5f5": bg_input = "#1f2937"
            if bg_hover == "#e2e8f0": bg_hover = "#4a5568"

        self.setStyleSheet(f"""
            QWidget {{ background: transparent; }}
            
            QLabel#FormLabel {{
                font-weight: bold; font-size: 12px; color: {text_sec};
            }}
            
            QLineEdit, QTextEdit {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 4px;
                color: {text_pri};
                padding: 5px;
            }}
            
            /* Sleek stitched Volume Control Styling */
            QPushButton#VolBtn {{
                background-color: {bg_input};
                border: 1px solid {border};
                color: {text_pri};
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton#VolBtn:hover {{
                background-color: {bg_hover};
            }}
            QDoubleSpinBox#VolInput {{
                background-color: {bg_input};
                border-top: 1px solid {border};
                border-bottom: 1px solid {border};
                border-left: none;
                border-right: none;
                color: {text_pri};
                border-radius: 0px;
            }}
            QDoubleSpinBox#VolInput::up-button, QDoubleSpinBox#VolInput::down-button {{
                width: 0px; /* Hide default arrows */
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
        # 🟢 FIX: Drastically reduced spacing and margins
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
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
        vol_label.setObjectName("FormLabel")
        
        # 🟢 FIX: Stitched Volume Control
        vol_control = QHBoxLayout()
        vol_control.setSpacing(0)
        
        vol_down = QPushButton("▼")
        vol_down.setObjectName("VolBtn")
        vol_down.setFixedSize(30, 32)
        
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setObjectName("VolInput")
        self.volume_input.setDecimals(2)
        self.volume_input.setMinimum(0.01)
        self.volume_input.setMaximum(100.0)
        self.volume_input.setSingleStep(0.01)
        self.volume_input.setValue(default_lot)
        self.volume_input.setAlignment(Qt.AlignCenter)
        self.volume_input.setFixedHeight(32)
        
        vol_up = QPushButton("▲")
        vol_up.setObjectName("VolBtn")
        vol_up.setFixedSize(30, 32)
        
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
        # 🟢 FIX: Reduced height from 40 to 32
        self.sl_input.setFixedHeight(32)
        
        self.tp_input = QLineEdit("Take Profit")
        self.tp_input.setAlignment(Qt.AlignCenter)
        # 🟢 FIX: Reduced height from 40 to 32
        self.tp_input.setFixedHeight(32)
        
        row.addWidget(self.sl_input)
        row.addWidget(self.tp_input)
        
        return row
    
    def _create_buttons_row(self):
        """Create Buy/Sell buttons"""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        # 🟢 FIX: Reduced height from 80 to 50
        self.sell_btn.setFixedHeight(50)
        self.sell_btn.setStyleSheet(BUTTON_STYLES['sell'])
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))
        
        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        # 🟢 FIX: Reduced height from 80 to 50
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
        # 🟢 FIX: Reduced remarks height
        self.remarks_input.setFixedHeight(45)
        
        layout.addWidget(label)
        layout.addWidget(self.remarks_input)
        
        return container
    
    def _create_info_row(self):
        """Create info labels row"""
        row = QHBoxLayout()
        row.setSpacing(15)
        
        info_labels = [
            ("Spread", "0.00"),
            ("Commission", "0"),
            ("Pip Value", "1"),
            ("Daily Swap USD", "Sell:  Buy:")
        ]
        
        for label_text, value_text in info_labels:
            container = QVBoxLayout()
            container.setSpacing(0)
            
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