from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QWidget, QSizePolicy,
    QGraphicsBlurEffect, QGraphicsScene, QGraphicsPixmapItem,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QPixmap, QColor
from MarketWatch_jetfyx.ui.components.market_order_form import MarketOrderForm
from MarketWatch_jetfyx.ui.components.limit_order_form import LimitOrderForm
from MarketWatch_jetfyx.config.ui_config import SIZES

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


# ======================================================================== #
#  Helpers                                                                  #
# ======================================================================== #
def _detect_dark() -> bool:
    from PySide6.QtGui import QColor
    import logging
    _log = logging.getLogger(__name__)

    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()

        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool):
                return val
            s = str(val).lower()
            if s in ("true", "1", "yes", "dark"):  return True
            if s in ("false", "0", "no", "light"): return False

        for key in ("bg_panel", "background", "bg_primary", "bg_base", "bg"):
            color_str = tok.get(key, None)
            if color_str:
                c = QColor(color_str)
                if c.isValid():
                    return c.lightness() < 128
    except Exception:
        pass

    try:
        app = QApplication.instance()
        if app:
            return app.palette().window().color().lightness() < 128
    except Exception:
        pass

    return False


def _accent() -> str:
    if _THEME_AVAILABLE:
        try:
            return ThemeManager.instance().tokens().get("accent", "#2563eb")
        except Exception:
            pass
    return "#2563eb"


# ======================================================================== #
#  Full-window blur overlay                                                 #
# ======================================================================== #
class _BlurOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setGeometry(parent.rect())
        self.raise_()
        raw = parent.grab()
        self._blurred = self._blur(raw, radius=20)

    @staticmethod
    def _blur(pixmap: QPixmap, radius: int) -> QPixmap:
        scene  = QGraphicsScene()
        item   = QGraphicsPixmapItem(pixmap)
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(radius)
        effect.setBlurHints(QGraphicsBlurEffect.QualityHint)
        item.setGraphicsEffect(effect)
        scene.addItem(item)
        out = QPixmap(pixmap.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        scene.render(p, source=QRect(0, 0, pixmap.width(), pixmap.height()))
        p.end()
        return out

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._blurred)
        p.fillRect(self.rect(), QColor(0, 0, 0, 100))
        p.end()


# ======================================================================== #
#  Order dialog                                                             #
# ======================================================================== #
class OrderDialog(QDialog):

    orderPlaced = Signal(str, str, float)

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01,
                 symbol_manager=None, order_service=None, parent=None):
        super().__init__(parent)

        self.symbol         = symbol
        self.sell_price     = sell_price
        self.buy_price      = buy_price
        self.symbol_manager = symbol_manager
        self.order_service  = order_service

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._S = 18                              # shadow padding
        self.setFixedSize(460 + self._S * 2, 420 + self._S * 2)

        self._drag_pos = None
        self._overlay  = None

        self.setup_ui(default_lot)
        self.apply_theme()

        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda *_: self.apply_theme()
                )
            except Exception:
                pass

        self._price_conn = False
        if self.symbol_manager:
            try:
                self.symbol_manager.priceUpdated.connect(self._on_price_update)
                self._price_conn = True
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Overlay
    # ------------------------------------------------------------------ #
    def showEvent(self, event):
        super().showEvent(event)
        self._install_overlay()

    def _install_overlay(self):
        target = self.parent()
        if target is None:
            return
        while target.parent() is not None:
            target = target.parent()
        self._remove_overlay()
        self._overlay = _BlurOverlay(target)
        self._overlay.show()

    def _remove_overlay(self):
        if self._overlay is not None:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    # ------------------------------------------------------------------ #
    # Drop-shadow paint
    # ------------------------------------------------------------------ #
    def paintEvent(self, event):
        s = self._S
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        for i in range(s, 0, -1):
            alpha = int(130 * (1 - i / s) ** 1.8)
            p.setBrush(QColor(0, 0, 0, alpha))
            p.drawRoundedRect(
                s - i, s - i,
                self.width()  - 2 * (s - i),
                self.height() - 2 * (s - i),
                11 + i * 0.3, 11 + i * 0.3
            )
        p.end()
        super().paintEvent(event)

    # ------------------------------------------------------------------ #
    # Drag
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'header_widget'):
            hr = self.header_widget.geometry().translated(self._S, self._S)
            if hr.contains(event.pos()):
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
    def apply_theme(self):
        s       = self._S
        dark    = _detect_dark()
        accent  = _accent()

        if dark:
            panel_bg  = "#151e2d"
            text_p    = "#e2e8f0"
            text_s    = "#94a3b8"
            border    = "#2d3a4a"
            btn_bg    = "#1e2a3a"
            btn_color = "#cbd5e1"
            hover_bg  = "#253347"
        else:
            panel_bg  = "#ffffff"
            text_p    = "#111827"
            text_s    = "#6b7280"
            border    = "#e2e8f0"
            btn_bg    = "#f8fafc"
            btn_color = "#374151"
            hover_bg  = "#f1f5f9"

        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}

            QFrame#MainContainer {{
                background-color: {panel_bg};
                border: 2px solid {accent};
                border-radius: 10px;
                margin: {s}px;
            }}

            QWidget#HeaderWidget  {{ background: transparent; }}
            QWidget#TabContainer  {{ background: transparent; }}

            QLabel {{
                background: transparent;
                color: {text_p};
            }}
            QLabel#SymbolLabel {{
                font-size: 15px; font-weight: 700;
                color: {text_p};
                letter-spacing: 0.5px;
            }}
            QLabel#SubtitleLabel {{
                font-size: 10px;
                color: {text_s};
            }}

            /* ── Header icon buttons ── */
            QPushButton#HdrBtn {{
                background-color: {btn_bg};
                border: 1px solid {border};
                border-radius: 4px;
                color: {btn_color};
                font-size: 10px; font-weight: 600;
                padding: 0px; margin: 0px;
            }}
            QPushButton#HdrBtn:hover {{
                background-color: {hover_bg};
                border-color: {accent};
                color: {accent};
            }}

            /* ── Close button ── */
            QPushButton#CloseBtn {{
                background-color: {btn_bg};
                border: 1px solid {border};
                border-radius: 4px;
                color: {btn_color};
                font-size: 12px; font-weight: 600;
                padding: 0px; margin: 0px;
            }}
            QPushButton#CloseBtn:hover {{
                background-color: #fee2e2;
                border-color: #ef4444;
                color: #ef4444;
            }}

            /* ── Tabs ── */
            QTabWidget::pane {{
                border: none;
                border-top: 1px solid {border};
                background: transparent;
            }}
            QTabWidget, QTabWidget > QWidget {{ background: transparent; }}
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
            QTabBar::tab:hover {{ color: {text_p}; }}
        """)

        # Push theme down to child forms
        try:
            self.market_form._apply_theme()
        except Exception:
            pass
        try:
            self.limit_form._apply_theme()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def setup_ui(self, default_lot):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        outer.addWidget(self.main_container)

        layout = QVBoxLayout(self.main_container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 8)

        self.header_widget = self._create_header()

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
        layout.addWidget(tab_container)

    def _create_header(self):
        hw = QWidget(self)
        hw.setObjectName("HeaderWidget")
        hw.setFixedHeight(52)

        vbox = QVBoxLayout(hw)
        vbox.setContentsMargins(12, 6, 12, 4)
        vbox.setSpacing(2)

        # Top row: [stretch | symbol ▾ ⓘ | stretch | ✕]
        top = QHBoxLayout()
        top.setSpacing(4)
        top.addStretch()

        sym_row = QHBoxLayout()
        sym_row.setSpacing(5)

        self.symbol_label = QLabel(self.symbol)
        self.symbol_label.setObjectName("SymbolLabel")

        self.symbol_dropdown = QPushButton("▾")
        self.symbol_dropdown.setObjectName("HdrBtn")
        self.symbol_dropdown.setFixedSize(20, 20)
        self.symbol_dropdown.clicked.connect(self.open_symbol_search)

        self.info_btn = QPushButton("i")
        self.info_btn.setObjectName("HdrBtn")
        self.info_btn.setFixedSize(20, 20)

        sym_row.addWidget(self.symbol_label)
        sym_row.addWidget(self.symbol_dropdown)
        sym_row.addWidget(self.info_btn)

        top.addLayout(sym_row)
        top.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject)
        top.addWidget(self.close_btn)

        # Subtitle
        self.subtitle_label = QLabel("Majors -Euro vs US Dollar")
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        vbox.addLayout(top)
        vbox.addWidget(self.subtitle_label)

        return hw

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
            self.buy_price  = buy
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
        self._remove_overlay()
        self._disconnect_price()
        return super().accept()

    def reject(self):
        self._remove_overlay()
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