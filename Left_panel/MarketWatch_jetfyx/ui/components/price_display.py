"""
Price Display Component - Reusable price display widget
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from MarketWatch_jetfyx.config.ui_config import COLORS


class PriceDisplay(QWidget):
    """Reusable component for displaying sell/buy prices"""
    
    def __init__(self, sell_price, buy_price, parent=None):
        super().__init__(parent)
        
        self.sell_price = sell_price
        self.buy_price = buy_price
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Sell price
        self.sell_label = QLabel(f"Sell: {self.sell_price}")
        self.sell_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['danger']};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        # Buy price
        self.buy_label = QLabel(f"Buy: {self.buy_price}")
        self.buy_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['success']};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        layout.addWidget(self.sell_label)
        layout.addWidget(self.buy_label)
        layout.addStretch()
    
    def update_prices(self, sell_price, buy_price):
        """Update displayed prices"""
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.sell_label.setText(f"Sell: {sell_price}")
        self.buy_label.setText(f"Buy: {buy_price}")
