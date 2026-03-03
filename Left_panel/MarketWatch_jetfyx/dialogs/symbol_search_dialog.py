from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


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
        self.apply_theme()
        self.load_symbols()

        # Live theme updates
        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

    def _tokens(self) -> dict:
        if _THEME_AVAILABLE:
            try:
                return ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    def apply_theme(self):
        t = self._tokens()

        bg         = t.get("bg_popup",        "#ffffff")
        text_p     = t.get("text_primary",    "#1a202c")
        border     = t.get("border_primary",  "#e5e7eb")
        border_f   = t.get("border_focus",    "#1976d2")
        accent     = t.get("accent",          "#1976d2")
        acc_t      = t.get("accent_text",     "#ffffff")
        bg_inp     = t.get("bg_input",        "#f5f7fa")
        bg_hover   = t.get("bg_row_hover",    "#e3f2fd")
        bg_sel     = t.get("bg_selected",     "#1565c0")
        sep        = t.get("border_separator","#e5e7eb")

        self.setStyleSheet(f"QDialog {{ background: {bg}; }}")

        if hasattr(self, "search_input"):
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: 10px;
                    background: {bg_inp};
                    color: {text_p};
                    border: 2px solid {border_f};
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QLineEdit:focus {{
                    border-color: {accent};
                }}
            """)

        if hasattr(self, "symbol_list"):
            self.symbol_list.setStyleSheet(f"""
                QListWidget {{
                    background: {bg};
                    color: {text_p};
                    border: 1px solid {border};
                    border-radius: 4px;
                    font-size: 13px;
                }}
                QListWidget::item {{
                    padding: 10px;
                    border-bottom: 1px solid {sep};
                    color: {text_p};
                }}
                QListWidget::item:hover {{
                    background: {bg_hover};
                }}
                QListWidget::item:selected {{
                    background: {bg_sel};
                    color: {acc_t};
                }}
            """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search symbols...")
        self.search_input.textChanged.connect(self.filter_symbols)

        self.symbol_list = QListWidget()
        self.symbol_list.itemDoubleClicked.connect(self.on_symbol_selected)

        layout.addWidget(self.search_input)
        layout.addWidget(self.symbol_list)

    def load_symbols(self):
        self.symbol_list.clear()
        all_symbols = self.symbol_manager.get_all_symbols()
        for symbol_data in all_symbols:
            symbol_name = None
            sell_price = ""
            buy_price = ""

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
        for i in range(self.symbol_list.count()):
            item = self.symbol_list.item(i)
            item_data = item.data(Qt.UserRole)
            symbol_name = item_data['name']
            item.setHidden(text.upper() not in symbol_name.upper())

    def on_symbol_selected(self, item):
        item_data = item.data(Qt.UserRole)
        self.symbolSelected.emit(
            item_data['name'],
            item_data['sell'],
            item_data['buy']
        )
        self.accept()