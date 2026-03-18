"""
Symbols are written as functions............

trade_panel.py  –  Trade panel with SELL/BUY buttons, lot control.

Changes (theme-aware):
  ✅ self.btn_close, self.btn_info, self.btn_favorite, self.btn_place_order stored
  ✅ self.btn_minus, self.btn_plus stored
  ✅ _apply_theme() added – called on init and on ThemeManager.theme_changed
  ✅ TradePanel background uses bg_widget + border_primary tokens
  ✅ SELL / BUY buttons keep their red/green colours (intentional, not themed)
  ✅ Zero hardcoded hex values in theme-critical UI controls
  ✅ Icons drawn as QPixmap (no Unicode/font dependency) – guaranteed to render
"""
from MarketWatch_jetfyx.widgets.lot_preset_widget import LotPresetWidget
from PySide6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QLabel, QLineEdit,
)
from PySide6.QtCore import Qt, Signal, QSize, QPointF
from PySide6.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath,
)
import math
import logging

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False

LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Icon factory – every icon is painted with QPainter; no font/glyph required
# ---------------------------------------------------------------------------

def _make_star_icon(filled: bool, size: int = 14) -> QIcon:
    """Gold filled star (favourite on) or grey outline star (favourite off)."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    cx, cy = size / 2.0, size / 2.0
    outer_r = size / 2.0 - 0.5
    inner_r = outer_r * 0.42

    path = QPainterPath()
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = outer_r if i % 2 == 0 else inner_r
        pt = QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle))
        if i == 0:
            path.moveTo(pt)
        else:
            path.lineTo(pt)
    path.closeSubpath()

    if filled:
        p.setBrush(QBrush(QColor("#FFA500")))
        p.setPen(QPen(QColor("#CC8400"), 0.8))
    else:
        p.setBrush(QBrush(QColor("#BBBBBB")))
        p.setPen(QPen(QColor("#888888"), 0.8))

    p.drawPath(path)
    p.end()
    return QIcon(px)


def _make_plus_icon(size: int = 14) -> QIcon:
    """White + on a green circle (New Order button)."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    cx, cy, r = size / 2.0, size / 2.0, size / 2.0 - 0.5
    p.setBrush(QBrush(QColor("#2e7d32")))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)

    pen = QPen(QColor("white"), max(1.5, size * 0.17), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    arm = r * 0.50
    p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
    p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

    p.end()
    return QIcon(px)


def _make_info_icon(size: int = 14) -> QIcon:
    """White 'i' on a blue circle (Info button)."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    cx, cy, r = size / 2.0, size / 2.0, size / 2.0 - 0.5
    p.setBrush(QBrush(QColor("#1565C0")))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)

    pen = QPen(QColor("white"), max(1.5, size * 0.17), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    # dot above
    p.drawPoint(QPointF(cx, cy - r * 0.32))
    # vertical stem
    p.drawLine(QPointF(cx, cy - r * 0.05), QPointF(cx, cy + r * 0.46))

    p.end()
    return QIcon(px)


def _make_close_icon(size: int = 14) -> QIcon:
    """White × on a grey circle (Close button)."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    cx, cy, r = size / 2.0, size / 2.0, size / 2.0 - 0.5
    p.setBrush(QBrush(QColor("#9E9E9E")))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)

    pen = QPen(QColor("white"), max(1.5, size * 0.17), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    arm = r * 0.42
    p.drawLine(QPointF(cx - arm, cy - arm), QPointF(cx + arm, cy + arm))
    p.drawLine(QPointF(cx + arm, cy - arm), QPointF(cx - arm, cy + arm))

    p.end()
    return QIcon(px)


def _apply_icon(btn: QPushButton, icon: QIcon, icon_size: int = 14):
    """Attach a painted icon to a QPushButton and clear any text."""
    btn.setText("")
    btn.setIcon(icon)
    btn.setIconSize(QSize(icon_size, icon_size))


# ---------------------------------------------------------------------------

class TradePanel(QWidget):
    closeRequested  = Signal()
    favoriteToggled = Signal(str, bool)

    _ICON_SIZE = 14   # pixel size of each icon drawn inside the 22×22 buttons

    def __init__(self, symbol, sell_price, buy_price,
                 symbol_manager=None, app_settings=None, order_service=None):
        super().__init__()
        # Required so setStyleSheet() actually fills the widget background,
        # covering the QTableView row colour painted behind this widget.
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.symbol         = symbol
        self.sell_price     = sell_price
        self.buy_price      = buy_price
        self.symbol_manager = symbol_manager
        self.app_settings   = app_settings or {}
        self.order_service  = order_service
        self.current_lot    = (
            self.app_settings.get("default_lot", 0.01)
            if self.app_settings.get("default_lot_enabled", False)
            else 0.01
        )
        self.is_favorite = symbol_manager.is_favorite(symbol) if symbol_manager else False

        # ---- Build UI ----
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -- Top bar --
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(6, 3, 6, 3)
        top_bar.setSpacing(4)

        self.symbol_label = QLabel(f"{symbol} ({sell_price})")
        self.symbol_label.setObjectName("TradePanelSymbol")

        # ★ Favourite button
        self.btn_favorite = QPushButton()
        self.btn_favorite.setFixedSize(22, 22)
        self.btn_favorite.setToolTip("Toggle Favourite")
        self.btn_favorite.clicked.connect(self.toggle_favorite)
        _apply_icon(self.btn_favorite,
                    _make_star_icon(self.is_favorite, self._ICON_SIZE),
                    self._ICON_SIZE)

        # + New-order button
        self.btn_place_order = QPushButton()
        self.btn_place_order.setFixedSize(22, 22)
        self.btn_place_order.setObjectName("TradeBtnPlus")
        self.btn_place_order.setToolTip("New Order")
        self.btn_place_order.clicked.connect(self.place_order)
        _apply_icon(self.btn_place_order,
                    _make_plus_icon(self._ICON_SIZE),
                    self._ICON_SIZE)

        # ⓘ Info button
        self.btn_info = QPushButton()
        self.btn_info.setFixedSize(22, 22)
        self.btn_info.setObjectName("TradeBtnIcon")
        self.btn_info.setToolTip("Symbol Info")
        _apply_icon(self.btn_info,
                    _make_info_icon(self._ICON_SIZE),
                    self._ICON_SIZE)

        # ✕ Close button
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.setObjectName("TradeBtnIcon")
        self.btn_close.setToolTip("Close Panel")
        self.btn_close.clicked.connect(self.closeRequested.emit)
        _apply_icon(self.btn_close,
                    _make_close_icon(self._ICON_SIZE),
                    self._ICON_SIZE)

        top_bar.addWidget(self.symbol_label)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_favorite)
        top_bar.addWidget(self.btn_place_order)
        top_bar.addWidget(self.btn_info)
        top_bar.addWidget(self.btn_close)

        # -- Trade layout --
        trade_layout = QHBoxLayout()
        trade_layout.setContentsMargins(8, 6, 8, 6)
        trade_layout.setSpacing(10)

        # SELL
        sell_box = QVBoxLayout()
        sell_box.setSpacing(2)
        sell_box.setAlignment(Qt.AlignCenter)

        self.sell_btn = QPushButton(f"SELL\n{sell_price}")
        self.sell_btn.setMinimumWidth(90)
        self.sell_btn.setMinimumHeight(45)
        self.sell_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sell_btn.setStyleSheet("""
            QPushButton {
                background: #e53935;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #c62828; }
        """)
        self.sell_btn.clicked.connect(self.on_sell_clicked)

        lower_label = QLabel("L - 1.16996")
        lower_label.setAlignment(Qt.AlignCenter)
        lower_label.setStyleSheet("color: #999; font-size: 9px;")

        sell_box.addWidget(self.sell_btn)
        sell_box.addWidget(lower_label)

        # LOT
        lot_box = QVBoxLayout()
        lot_box.setAlignment(Qt.AlignCenter)
        lot_box.setSpacing(4)

        lot_control = QHBoxLayout()
        lot_control.setSpacing(3)

        self.btn_minus = QPushButton("−")
        self.btn_minus.setFixedSize(18, 21)
        self.btn_minus.clicked.connect(self.decrease_lot)

        self.lot_display = QLineEdit()
        self.lot_display.setText(f"{self.current_lot:.2f}")
        self.lot_display.setAlignment(Qt.AlignCenter)
        self.lot_display.setFixedSize(46, 21)
        self.lot_display.setObjectName("LotDisplay")
        self.lot_display.textChanged.connect(self.on_lot_text_changed)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(18, 21)
        self.btn_plus.clicked.connect(self.increase_lot)

        lot_control.addWidget(self.btn_minus)
        lot_control.addWidget(self.lot_display)
        lot_control.addWidget(self.btn_plus)

        self.lot_widget = LotPresetWidget()
        lot_box.addLayout(lot_control)
        lot_box.addWidget(self.lot_widget)

        # BUY
        buy_box = QVBoxLayout()
        buy_box.setSpacing(2)
        buy_box.setAlignment(Qt.AlignCenter)

        self.buy_btn = QPushButton(f"BUY\n{buy_price}")
        self.buy_btn.setMinimumWidth(90)
        self.buy_btn.setMinimumHeight(45)
        self.buy_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background: #2e7d32;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #1b5e20; }
        """)
        self.buy_btn.clicked.connect(self.on_buy_clicked)

        higher_label = QLabel("H - 1.17430")
        higher_label.setAlignment(Qt.AlignCenter)
        higher_label.setStyleSheet("color: #999; font-size: 9px;")

        buy_box.addWidget(self.buy_btn)
        buy_box.addWidget(higher_label)

        trade_layout.addStretch()
        trade_layout.addLayout(sell_box)
        trade_layout.addLayout(lot_box)
        trade_layout.addLayout(buy_box)
        trade_layout.addStretch()

        main_layout.addLayout(top_bar)
        main_layout.addLayout(trade_layout)

        # Apply initial theme + connect signal
        self._apply_theme()
        if _THEME_AVAILABLE:
            try:
                def _on_trade_panel_theme_changed(name, t):
                    try:
                        self._apply_theme()
                    except RuntimeError:
                        pass
                ThemeManager.instance().theme_changed.connect(_on_trade_panel_theme_changed)
            except Exception:
                pass

        if self.symbol_manager and hasattr(self.symbol_manager, "priceUpdated"):
            self.symbol_manager.priceUpdated.connect(self.on_price_update)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _apply_theme(self):
        """Re-style all themed controls using current tokens."""
        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
            except Exception:
                t = {}
        else:
            t = {}

        # Detect dark/light for proper fallbacks
        _dark = False
        try:
            val = t.get("is_dark", None)
            if val is not None:
                _dark = str(val).lower() in ("true", "1", "yes", "dark")
            else:
                from PySide6.QtGui import QColor as _QC
                for k in ("bg_panel", "background", "bg_primary"):
                    cs = t.get(k)
                    if cs:
                        _dark = _QC(cs).lightness() < 128
                        break
        except Exception:
            pass

        def _t(*keys, fd, fl):
            for k in keys:
                v = t.get(k)
                if v: return v
            return fd if _dark else fl

        bg_widget  = _t("bg_widget", "bg_panel", "background",
                        fd="#1e2a3a", fl="#ffffff")
        border_p   = _t("border_primary", "border", "border_color",
                        fd="#2d3a4a", fl="#e2e8f0")
        text_p     = _t("text_primary", "text", "fg",
                        fd="#e2e8f0", fl="#1a202c")
        accent     = _t("accent", "primary", "color_accent",
                        fd="#3b82f6", fl="#1976d2")
        bg_btn     = _t("bg_button", "bg_input", "bg_secondary",
                        fd="#253347", fl="#f0f4f8")
        bg_btn_h   = _t("bg_button_hover", "bg_hover",
                        fd="#1e2d3d", fl="#e2e8f0")
        bg_input   = _t("bg_input", "bg_secondary", "bg_surface",
                        fd="#1e2a3a", fl="#ffffff")
        border_foc = _t("border_focus", "accent", "primary",
                        fd="#3b82f6", fl="#1976d2")

        # Panel background — must cover the table row behind it fully
        self.setStyleSheet(f"""
            TradePanel {{
                background-color: {bg_widget};
                border: 1px solid {border_p};
                border-radius: 0px;
            }}
        """)

        # Symbol label
        self.symbol_label.setStyleSheet(f"""
            QLabel {{
                color: {accent};
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }}
        """)

        # Icon buttons – transparent background, light border; icon supplies the colour
        icon_ss = f"""
            QPushButton {{
                background: {bg_btn};
                border: 1px solid {border_p};
                border-radius: 3px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {bg_btn_h};
                border: 1px solid {accent};
            }}
            QPushButton:pressed {{
                background: {bg_btn};
            }}
        """
        self.btn_favorite.setStyleSheet(icon_ss)
        self.btn_place_order.setStyleSheet(icon_ss)
        self.btn_info.setStyleSheet(icon_ss)
        self.btn_close.setStyleSheet(icon_ss)

        # − / + lot buttons
        lot_ss = f"""
            QPushButton {{
                background: {bg_btn};
                color: {text_p};
                border: 1px solid {border_p};
                border-radius: 3px;
                font-size: 16px;
                font-weight: 900;
                padding: 0px;
            }}
            QPushButton:hover {{ background: {bg_btn_h}; color: {text_p}; }}
        """
        self.btn_minus.setStyleSheet(lot_ss)
        self.btn_plus.setStyleSheet(lot_ss)

        # Lot display input
        self.lot_display.setStyleSheet(f"""
            QLineEdit {{
                background: {bg_input};
                border: 2px solid {border_foc};
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                color: {text_p};
                padding: 0px;
            }}
        """)

    # ------------------------------------------------------------------
    # Lot control
    # ------------------------------------------------------------------
    def increase_lot(self):
        selected = self.lot_widget.get_selected_lot()
        self.current_lot = min(100, self.current_lot + selected)
        self.lot_display.setText(f"{self.current_lot:.2f}")

    def decrease_lot(self):
        selected = self.lot_widget.get_selected_lot()
        self.current_lot = max(0.01, self.current_lot - selected)
        self.lot_display.setText(f"{self.current_lot:.2f}")

    def on_lot_text_changed(self, text):
        try:
            value = float(text)
            if 0.01 <= value <= 100:
                self.current_lot = value
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Favourite
    # ------------------------------------------------------------------
    def toggle_favorite(self):
        self.is_favorite = not self.is_favorite
        if self.symbol_manager:
            self.symbol_manager.toggle_favorite(self.symbol)
        self.favoriteToggled.emit(self.symbol, self.is_favorite)
        # Repaint star icon to reflect new state
        _apply_icon(self.btn_favorite,
                    _make_star_icon(self.is_favorite, self._ICON_SIZE),
                    self._ICON_SIZE)

    def _update_favorite_style(self):
        """Kept for backward compatibility."""
        _apply_icon(self.btn_favorite,
                    _make_star_icon(self.is_favorite, self._ICON_SIZE),
                    self._ICON_SIZE)

    # ------------------------------------------------------------------
    # Order actions
    # ------------------------------------------------------------------
    def on_sell_clicked(self):
        one_click = self.app_settings.get("one_click_trade", False)
        LOG.info("SELL clicked: symbol=%s lot=%s one_click=%s", self.symbol, self.current_lot, one_click)
        if one_click and self.order_service:
            result = self.order_service.place_market_order(self.symbol, "SELL", self.current_lot)
            LOG.info("SELL via OrderService: %s", result)
        else:
            self.open_order_dialog("SELL")

    def on_buy_clicked(self):
        one_click = self.app_settings.get("one_click_trade", False)
        LOG.info("BUY clicked: symbol=%s lot=%s one_click=%s", self.symbol, self.current_lot, one_click)
        if one_click and self.order_service:
            result = self.order_service.place_market_order(self.symbol, "BUY", self.current_lot)
            LOG.info("BUY via OrderService: %s", result)
        else:
            self.open_order_dialog("BUY")

    def open_order_dialog(self, order_type):
        from MarketWatch_jetfyx.dialogs.order_dialog import OrderDialog
        default_lot = (
            self.app_settings.get("default_lot", 0.01)
            if self.app_settings.get("default_lot_enabled", False)
            else self.current_lot
        )
        dialog = OrderDialog(
            self.symbol, self.sell_price, self.buy_price,
            default_lot, self.symbol_manager, self.order_service, self,
        )
        dialog.orderPlaced.connect(
            lambda ot, s, v: LOG.info("Order placed: %s %s %s", ot, s, v)
        )
        dialog.exec()

    def place_order(self):
        self.open_order_dialog("BUY")

    def update_prices(self, sell_price, buy_price, hub_received_timestamp=None):
        import time
        self.sell_price = sell_price
        self.buy_price  = buy_price
        self.sell_btn.setText(f"SELL\n{sell_price}")
        self.buy_btn.setText(f"BUY\n{buy_price}")
        self.symbol_label.setText(f"{self.symbol} ({sell_price})")
        if hub_received_timestamp:
            latency = (time.time() - hub_received_timestamp) * 1000
            LOG.debug("[Latency] TradePanel %s = %.2f ms", self.symbol, latency)

    def on_price_update(self, symbol, sell, buy):
        if symbol != self.symbol:
            return
        self.update_prices(sell, buy)