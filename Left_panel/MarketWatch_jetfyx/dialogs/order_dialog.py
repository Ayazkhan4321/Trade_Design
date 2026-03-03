from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QWidget
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

    orderPlaced = Signal(str, str, float)  # order_type, symbol, volume

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01,
                 symbol_manager=None, order_service=None, parent=None):
        super().__init__(parent)

        self.symbol = symbol
        self.sell_price = sell_price
        self.buy_price = buy_price
        self.symbol_manager = symbol_manager
        self.order_service = order_service

        # 🟢 FIX: Remove OS Title bar and make background translucent
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(SIZES['dialog_width'], SIZES['dialog_height'])
        
        self._drag_pos = None

        self.setup_ui(default_lot)
        self.apply_theme()

        # Live theme updates
        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

        # Connect to live price updates
        self._price_conn = False
        if self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.connect(self._on_price_update)
                self._price_conn = True
            except Exception:
                self._price_conn = False

    # ------------------------------------------------------------------ #
    # Custom Drag Logic for Frameless Window                                #
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'header_widget') and self.header_widget.geometry().contains(event.pos()):
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
    # Theme                                                                #
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

        bg       = t.get("bg_panel",        "#ffffff") 
        text_p   = t.get("text_primary",    "#1a202c")
        text_s   = t.get("text_secondary",  "#4a5568")
        border   = t.get("border_primary",  "#e5e7eb")
        accent   = t.get("accent",          "#1976d2")
        is_dark  = t.get("is_dark", "false") == "true"
        
        # Safe contrast for header text
        acc_t    = "#ffffff" if is_dark else t.get("accent_text", "#ffffff")
        if "crazy" in t.get("current_theme", "") or not is_dark:
            acc_t = "#ffffff"
            
        bg_hover = t.get("bg_button_hover", "#e2e8f0")
        
        # Enforce dark mode specific fixes if tokens are weak
        if is_dark:
            if border == "#e5e7eb": border = "#374151"
            if bg_hover == "#e2e8f0": bg_hover = "#4a5568"

        # Main Container
        self.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {bg};
                border: 2px solid {accent};
                border-radius: 8px;
            }}
            QWidget#HeaderWidget {{
                background-color: {accent};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QLabel {{
                background: transparent;
                color: {text_p};
            }}
        """)

        # Symbol label
        if hasattr(self, "symbol_label"):
            self.symbol_label.setStyleSheet(
                f"font-size: 20px; font-weight: bold; color: {acc_t}; background: transparent;"
            )

        # Subtitle
        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setStyleSheet(
                f"color: {acc_t}; font-size: 12px; background: transparent; opacity: 0.85;"
            )

        # 🟢 FIX: Modernized Tabs. No background blocks, just clean bottom-borders for better dark mode!
        if hasattr(self, "tabs"):
            self.tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: none;
                    border-top: 1px solid {border};
                    background: transparent;
                }}
                QTabBar::tab {{
                    padding: 8px 30px;
                    font-size: 13px;
                    font-weight: 600;
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

        # Symbol dropdown button
        if hasattr(self, "symbol_dropdown"):
            self.symbol_dropdown.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                    color: {acc_t};
                }}
                QPushButton:hover {{
                    background: rgba(0,0,0,0.15);
                    border-color: {acc_t};
                }}
            """)

        # Info button
        if hasattr(self, "info_btn"):
            self.info_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                    color: {acc_t};
                }}
                QPushButton:hover {{
                    background: rgba(0,0,0,0.15);
                }}
            """)

        # Close button (Massively increased font size!)
        if hasattr(self, "close_btn"):
            self.close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 24px;  
                    font-weight: bold;
                    color: {acc_t};
                }}
                QPushButton:hover {{
                    background: rgba(0,0,0,0.15);
                }}
            """)

    # ------------------------------------------------------------------ #
    # UI construction                                                       #
    # ------------------------------------------------------------------ #
    def setup_ui(self, default_lot):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        outer_layout.addWidget(self.main_container)

        layout = QVBoxLayout(self.main_container)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 15)

        self.header_widget = self._create_header()

        self.subtitle_label = QLabel("Majors -Euro vs US Dollar")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.tabs = QTabWidget()
        
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(15, 0, 15, 0)
        tab_layout.addWidget(self.tabs)

        self.market_form = MarketOrderForm(
            self.symbol, self.sell_price, self.buy_price, default_lot, self
        )
        self.market_form.orderSubmitted.connect(self.handle_market_order)

        self.limit_form = LimitOrderForm(
            self.symbol, self.sell_price, self.buy_price, default_lot, self
        )
        self.limit_form.orderSubmitted.connect(self.handle_limit_order)

        self.tabs.addTab(self.market_form, "Market Order")
        self.tabs.addTab(self.limit_form, "Limit / Stop Order")

        layout.addWidget(self.header_widget)
        
        # We put subtitle inside the dark header visually
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(self.subtitle_label)
        self.header_widget.layout().addLayout(subtitle_layout)

        layout.addWidget(tab_container)

    def _create_header(self):
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        
        main_header_layout = QVBoxLayout(header_widget)
        main_header_layout.setContentsMargins(15, 10, 15, 10)
        main_header_layout.setSpacing(5)
        
        header = QHBoxLayout()
        header.addStretch()

        symbol_container = QHBoxLayout()
        symbol_container.setSpacing(8)

        self.symbol_label = QLabel(self.symbol)

        # 🟢 FIX: Used highly compatible characters to prevent missing font boxes
        self.symbol_dropdown = QPushButton("▼")
        self.symbol_dropdown.setFixedSize(30, 30)
        self.symbol_dropdown.clicked.connect(self.open_symbol_search)

        self.info_btn = QPushButton("i")
        self.info_btn.setFixedSize(30, 30)

        symbol_container.addWidget(self.symbol_label)
        symbol_container.addWidget(self.symbol_dropdown)
        symbol_container.addWidget(self.info_btn)

        header.addLayout(symbol_container)
        header.addStretch()

        # 🟢 FIX: Capital "X", 36x36 size for easy clicking
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject)

        header.addWidget(self.close_btn)
        main_header_layout.addLayout(header)
        
        return header_widget

    # ------------------------------------------------------------------ #
    # Behaviour                                                             #
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
                order_data['symbol'],
                order_data['type'],
                order_data['volume'],
                order_data.get('stop_loss'),
                order_data.get('take_profit'),
                order_data.get('remarks', '')
            )
        else:
            print(f"Market {order_data['type']} - Symbol: {order_data['symbol']}, "
                  f"Volume: {order_data['volume']}")
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()

    def handle_limit_order(self, order_data):
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
            print(f"Limit {order_data['type']} - Symbol: {order_data['symbol']}, "
                  f"Volume: {order_data['volume']}, Entry: {order_data.get('entry_price')}")
        self.orderPlaced.emit(order_data['type'], order_data['symbol'], order_data['volume'])
        self.accept()