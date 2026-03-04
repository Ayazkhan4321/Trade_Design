from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint
from MarketWatch_jetfyx.ui.components.market_order_form import MarketOrderForm
from MarketWatch_jetfyx.ui.components.limit_order_form import LimitOrderForm
from MarketWatch_jetfyx.config.ui_config import SIZES

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class OrderDialog(QDialog):
    """Dialog for placing orders - uses modular form components"""

    orderPlaced = Signal(str, str, float)

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01,
                 symbol_manager=None, order_service=None, parent=None):
        super().__init__(parent)

        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.symbol_manager = symbol_manager
        self.order_service = order_service

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(460, 420)

        self._drag_pos = None

        self.setup_ui(default_lot)
        self.apply_theme()

        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

        self._price_conn = False
        if self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.connect(self._on_price_update)
                self._price_conn = True
            except Exception:
                self._price_conn = False

    # ------------------------------------------------------------------ #
    # Drag
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'header_widget') and \
                self.header_widget.geometry().contains(event.pos()):
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #
    def _tokens(self) -> dict:
        if _THEME_AVAILABLE:
            try:
                return ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    def apply_theme(self):
        t = self._tokens()

        bg      = t.get("bg_panel",        "#ffffff")
        text_p  = t.get("text_primary",    "#1a202c")
        text_s  = t.get("text_secondary",  "#4a5568")
        border  = t.get("border_primary",  "#e5e7eb")
        accent  = t.get("accent",          "#1976d2")
        is_dark = t.get("is_dark", "false") == "true"

        acc_t    = "#ffffff"
        bg_hover = t.get("bg_button_hover", "#e2e8f0")

        if is_dark:
            if border   == "#e5e7eb": border   = "#374151"
            if bg_hover == "#e2e8f0": bg_hover = "#4a5568"

        self.setStyleSheet(f"""
            QDialog {{
                background: transparent;
            }}

            QFrame#MainContainer {{
                background-color: {bg};
                border: 2px solid {accent};
                border-radius: 8px;
            }}

            QWidget#HeaderWidget {{
                background-color: {accent};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QWidget#TabContainer {{
                background: transparent;
            }}

            QLabel {{
                background: transparent;
                color: {text_p};
            }}

            QLabel#SymbolLabel {{
                font-size: 16px; font-weight: bold;
                color: #ffffff; background: transparent;
            }}
            QLabel#SubtitleLabel {{
                font-size: 11px; color: #ffffff; background: transparent;
            }}

            /* 🟢 FIX: Stripped native padding so the icons fit perfectly inside the boxes */
            QPushButton#HdrBtn {{
                background-color: rgba(255,255,255,0.22);
                border: 2px solid #ffffff;
                border-radius: 5px;
                color: #ffffff;
                font-family: "Segoe UI Symbol", Arial, sans-serif;
                font-size: 12px; 
                font-weight: 900;
                padding: 0px;
                margin: 0px;
                text-align: center;
            }}
            QPushButton#HdrBtn:hover {{
                background-color: rgba(255,255,255,0.40);
            }}

            QPushButton#CloseBtn {{
                background-color: rgba(255,255,255,0.22);
                border: 2px solid #ffffff;
                border-radius: 5px;
                color: #ffffff;
                font-family: "Segoe UI Symbol", Arial, sans-serif;
                font-size: 14px; 
                font-weight: 900;
                padding: 0px;
                margin: 0px;
                text-align: center;
            }}
            QPushButton#CloseBtn:hover {{
                background-color: rgba(210,40,40,0.88);
                border-color: #ffffff;
            }}

            QTabWidget::pane {{
                border: none;
                border-top: 1px solid {border};
                background: transparent;
            }}
            QTabWidget, QTabWidget > QWidget {{
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 6px 20px;
                font-size: 12px; font-weight: 600;
                color: {text_s};
                background: transparent;
                border: none;
                border-bottom: 3px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {accent};
                border-bottom: 3px solid {accent};
            }}
            QTabBar::tab:hover {{
                color: {text_p};
            }}
        """)

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def setup_ui(self, default_lot):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        outer_layout.addWidget(self.main_container)

        layout = QVBoxLayout(self.main_container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 10)

        self.header_widget = self._create_header()

        self.subtitle_label = QLabel("Majors -Euro vs US Dollar")
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        tab_container = QWidget()
        tab_container.setObjectName("TabContainer")
        tab_layout = QVBoxLayout(tab_container)
        
        tab_layout.setContentsMargins(10, 0, 10, 0)
        tab_layout.setSpacing(0)
        tab_layout.addWidget(self.tabs)
        tab_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.market_form = MarketOrderForm(
            self.symbol, self.sell_price, self.buy_price, default_lot, self)
        self.market_form.orderSubmitted.connect(self.handle_market_order)

        self.limit_form = LimitOrderForm(
            self.symbol, self.sell_price, self.buy_price, default_lot, self)
        self.limit_form.orderSubmitted.connect(self.handle_limit_order)

        self.tabs.addTab(self.market_form, "Market Order")
        self.tabs.addTab(self.limit_form, "Limit / Stop Order")

        layout.addWidget(self.header_widget)

        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(self.subtitle_label)
        self.header_widget.layout().addLayout(subtitle_layout)

        layout.addWidget(tab_container)

    def _create_header(self):
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")

        main_header_layout = QVBoxLayout(header_widget)
        main_header_layout.setContentsMargins(12, 8, 12, 6)
        main_header_layout.setSpacing(2)

        header = QHBoxLayout()
        header.addStretch()

        symbol_container = QHBoxLayout()
        symbol_container.setSpacing(6)

        self.symbol_label = QLabel(self.symbol)
        self.symbol_label.setObjectName("SymbolLabel")

        # 🟢 FIX: Beautiful solid arrow symbol
        self.symbol_dropdown = QPushButton("▼")
        self.symbol_dropdown.setObjectName("HdrBtn")
        self.symbol_dropdown.setFixedSize(26, 26)
        self.symbol_dropdown.clicked.connect(self.open_symbol_search)

        self.info_btn = QPushButton("i")
        self.info_btn.setObjectName("HdrBtn")
        self.info_btn.setFixedSize(26, 26)

        symbol_container.addWidget(self.symbol_label)
        symbol_container.addWidget(self.symbol_dropdown)
        symbol_container.addWidget(self.info_btn)

        header.addLayout(symbol_container)
        header.addStretch()

        # 🟢 FIX: Beautiful crisp cross symbol
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject)

        header.addWidget(self.close_btn)
        main_header_layout.addLayout(header)

        return header_widget

    # ------------------------------------------------------------------ #
    # Behaviour (unchanged)
    # ------------------------------------------------------------------ #
    def open_symbol_search(self):
        from MarketWatch_jetfyx.dialogs.symbol_search_dialog import SymbolSearchDialog
        if not self.symbol_manager:
            return
        dialog = SymbolSearchDialog(self.symbol_manager, self)
        dialog.symbolSelected.connect(self.change_symbol)
        dialog.exec()

    def change_symbol(self, symbol_name, sell_price, buy_price):
        self.symbol = symbol_name
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.symbol_label.setText(symbol_name)
        self.market_form.update_prices(sell_price, buy_price)
        self.limit_form.update_prices(sell_price, buy_price)

    def _on_price_update(self, symbol_name, sell, buy):
        if symbol_name != self.symbol:
            return
        try:
            self.market_form.update_prices(sell, buy)
            self.limit_form.update_prices(sell, buy)
            self.sell_price = sell
            self.buy_price = buy
        except Exception:
            pass

    def _disconnect_price(self):
        if getattr(self, '_price_conn', False) and self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.disconnect(self._on_price_update)
            except Exception:
                pass
            self._price_conn = False

    def accept(self):
        self._disconnect_price()
        return super().accept()

    def reject(self):
        self._disconnect_price()
        return super().reject()

    def handle_market_order(self, order_data):
        if self.order_service:
            self.order_service.place_market_order(
                order_data['symbol'], order_data['type'], order_data['volume'],
                order_data.get('stop_loss'), order_data.get('take_profit'),
                order_data.get('remarks', ''))
        else:
            print(f"Market {order_data['type']} - {order_data['symbol']} vol:{order_data['volume']}")
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()

    def handle_limit_order(self, order_data):
        if self.order_service:
            self.order_service.place_limit_order(
                order_data['symbol'], order_data['type'], order_data['volume'],
                order_data.get('entry_price'), order_data.get('stop_loss'),
                order_data.get('take_profit'))
        else:
            print(f"Limit {order_data['type']} - {order_data['symbol']} vol:{order_data['volume']}")
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()