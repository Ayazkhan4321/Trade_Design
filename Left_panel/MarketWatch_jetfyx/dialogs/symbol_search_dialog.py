from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal


class SymbolSearchDialog(QDialog):
    """Dialog for searching and selecting symbols"""
    
    symbolSelected = Signal(str, str, str)  # symbol_name, sell_price, buy_price
    
    def __init__(self, symbol_manager, parent=None):
        super().__init__(parent)
        
        self.symbol_manager = symbol_manager
        
        self.setWindowTitle("Select Symbol")
        self.setModal(True)
        self.setFixedSize(350, 450)
        
        self.setup_ui()
        self.load_symbols()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search symbols...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #1976d2;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_symbols)
        
        # Symbol list
        self.symbol_list = QListWidget()
        self.symbol_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }
        """)
        self.symbol_list.itemDoubleClicked.connect(self.on_symbol_selected)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.symbol_list)
    
    def load_symbols(self):
        """Load all symbols into the list"""
        self.symbol_list.clear()
        all_symbols = self.symbol_manager.get_all_symbols()
        for symbol_data in all_symbols:
            symbol_name = None
            sell_price = ""
            buy_price = ""

            # Support either dict-based symbols (SymbolManager) or tuple/list rows
            if isinstance(symbol_data, dict):
                symbol_name = symbol_data.get('symbol') or symbol_data.get('name')
                sell_price = symbol_data.get('sell', "")
                buy_price = symbol_data.get('buy', "")
            elif isinstance(symbol_data, (list, tuple)) and len(symbol_data) >= 3:
                try:
                    symbol_name = symbol_data[0]
                    sell_price = symbol_data[1]
                    buy_price = symbol_data[2]
                except Exception:
                    continue
            else:
                # Unknown format - skip
                continue

            if not symbol_name:
                continue

            item = QListWidgetItem(f"{symbol_name}  •  {sell_price} / {buy_price}")
            item.setData(Qt.UserRole, {
                'name': symbol_name,
                'sell': sell_price,
                'buy': buy_price
            })
            self.symbol_list.addItem(item)
    
    def filter_symbols(self, text):
        """Filter symbols based on search text"""
        for i in range(self.symbol_list.count()):
            item = self.symbol_list.item(i)
            item_data = item.data(Qt.UserRole)
            symbol_name = item_data['name']
            
            if text.upper() in symbol_name.upper():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def on_symbol_selected(self, item):
        """Handle symbol selection"""
        item_data = item.data(Qt.UserRole)
        self.symbolSelected.emit(
            item_data['name'],
            item_data['sell'],
            item_data['buy']
        )
        self.accept()
