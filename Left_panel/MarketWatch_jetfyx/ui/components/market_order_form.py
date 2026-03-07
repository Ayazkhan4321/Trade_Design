"""
Market Order Form Component
Layout matches reference: Volume | Contract Value | Margin on one row,
Stop Loss | [gap] | Take Profit on second row, Sell/Buy buttons below.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QDoubleSpinBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES
import logging

LOG = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────
def _detect_dark() -> bool:
    """
    Bulletproof dark detection — 3 independent methods:
    1. ThemeManager is_dark token (bool or string)
    2. ThemeManager bg_panel color luminance
    3. QPalette window color luminance
    """
    from PySide6.QtGui import QColor

    # Method 1 & 2 — ThemeManager
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()

        # 1a: explicit is_dark key
        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool):
                LOG.debug("_detect_dark via is_dark bool: %s", val)
                return val
            s = str(val).lower()
            if s in ("true", "1", "yes", "dark"):
                LOG.debug("_detect_dark via is_dark str: %s", s)
                return True
            if s in ("false", "0", "no", "light"):
                LOG.debug("_detect_dark via is_dark str: %s", s)
                return False

        # 1b: check bg_panel / background color lightness
        for key in ("bg_panel", "background", "bg_primary", "bg_base", "bg"):
            color_str = tok.get(key, None)
            if color_str:
                c = QColor(color_str)
                if c.isValid():
                    result = c.lightness() < 128
                    LOG.debug("_detect_dark via token '%s'=%s lightness=%d → %s",
                              key, color_str, c.lightness(), result)
                    return result
    except Exception as e:
        LOG.debug("_detect_dark ThemeManager failed: %s", e)

    # Method 3 — QPalette
    try:
        app = QApplication.instance()
        if app:
            c = app.palette().window().color()
            result = c.lightness() < 128
            LOG.debug("_detect_dark via QPalette lightness=%d → %s", c.lightness(), result)
            return result
    except Exception as e:
        LOG.debug("_detect_dark QPalette failed: %s", e)

    return False


def _accent() -> str:
    try:
        from Theme.theme_manager import ThemeManager
        return ThemeManager.instance().tokens().get("accent", "#2563eb")
    except Exception:
        return "#2563eb"


# ── PlaceholderSpinBox ────────────────────────────────────────────────────
class PlaceholderSpinBox(QDoubleSpinBox):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self._placeholder = placeholder
        self.setSpecialValueText(self._placeholder)

    def focusInEvent(self, event):
        self.setSpecialValueText("")
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def focusOutEvent(self, event):
        if self.value() == self.minimum():
            self.setSpecialValueText(self._placeholder)
        super().focusOutEvent(event)


# ── MarketOrderForm ───────────────────────────────────────────────────────
class MarketOrderForm(QWidget):

    orderSubmitted = Signal(dict)

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, parent=None):
        super().__init__(parent)
        self.symbol     = symbol
        self.sell_price = sell_price
        self.buy_price  = buy_price

        self.setup_ui(default_lot)
        self._apply_theme()

        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda *_: self._apply_theme())
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #
    def _apply_theme(self):
        dark   = _detect_dark()
        accent = _accent()

        if dark:
            bg_card     = "#151e2d"   # same as dialog panel so it blends
            bg_input    = "#1e2a3a"
            text_pri    = "#e2e8f0"
            text_sec    = "#94a3b8"
            border      = "#2d3a4a"
            arrow_bg    = "#253347"
            arrow_color = "#cbd5e1"
        else:
            bg_card     = "#ffffff"
            bg_input    = "#f9fafb"
            text_pri    = "#111827"
            text_sec    = "#6b7280"
            border      = "#e2e8f0"
            arrow_bg    = "#f3f4f6"
            arrow_color = "#374151"

        self.setStyleSheet(f"""
            MarketOrderForm {{ background: transparent; }}
            QWidget {{ background: transparent; }}

            /* ── Section labels: VOLUME / CONTRACT VALUE / MARGIN ── */
            QLabel#FormLabel {{
                font-size: 9px;
                font-weight: 700;
                color: {text_sec};
                letter-spacing: 0.8px;
                background: transparent;
            }}

            /* ── Read-only display boxes ── */
            QLabel#FormValue {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 5px;
                font-size: 11px;
                color: {text_pri};
                padding: 2px 6px;
            }}

            /* ── Remarks ── */
            QTextEdit {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 5px;
                font-size: 11px;
                color: {text_pri};
                padding: 4px 6px;
            }}
            QTextEdit:focus {{ border: 1px solid {accent}; }}

            /* ── Arrow buttons ── */
            QPushButton#StitchedBtnLeft,
            QPushButton#StitchedBtnRight {{
                background-color: {arrow_bg};
                border: 1px solid {border};
                color: {arrow_color};
                font-size: 10px;
                font-weight: 700;
                padding: 0px; margin: 0px;
            }}
            QPushButton#StitchedBtnLeft:hover,
            QPushButton#StitchedBtnRight:hover {{
                background-color: {accent};
                color: #ffffff;
                border-color: {accent};
            }}
            QPushButton#StitchedBtnLeft {{
                border-top-left-radius: 5px;
                border-bottom-left-radius: 5px;
                border-right: none;
            }}
            QPushButton#StitchedBtnRight {{
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                border-left: none;
            }}

            /* ── Spinbox center input ── */
            QDoubleSpinBox#StitchedInput {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 0px;
                color: {text_pri};
                font-size: 12px;
                font-weight: 600;
            }}
            QDoubleSpinBox#StitchedInput:focus {{
                border-top: 1px solid {accent};
                border-bottom: 1px solid {accent};
            }}
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {{
                width: 0px; border: none; background: transparent;
            }}

            /* ── Separator ── */
            QFrame#Separator {{
                background-color: {border};
                max-height: 1px; border: none;
            }}

            /* ── Info strip ── */
            QLabel#InfoLabel {{
                font-size: 9px; color: {text_sec};
                letter-spacing: 0.3px; background: transparent;
            }}
            QLabel#InfoValue {{
                font-size: 10px; color: {text_pri};
                font-weight: 600; background: transparent;
            }}
        """)

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def setup_ui(self, default_lot):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(10, 8, 10, 6)

        layout.addLayout(self._create_top_row(default_lot))
        layout.addSpacing(8)
        layout.addLayout(self._create_sl_tp_row())
        layout.addSpacing(10)
        layout.addLayout(self._create_buttons_row())
        layout.addSpacing(8)
        layout.addWidget(self._create_remarks_section())
        layout.addSpacing(6)
        layout.addWidget(self._make_separator())
        layout.addSpacing(6)
        layout.addLayout(self._create_info_row())

        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _make_separator(self):
        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        return sep

    # ── Row 1: Volume | Contract Value | Margin ─────────────────────────
    def _create_top_row(self, default_lot):
        row = QHBoxLayout()
        row.setSpacing(8)

        # — Volume column —
        vol_col = QVBoxLayout()
        vol_col.setSpacing(4)

        vol_label = QLabel("Volume")
        vol_label.setObjectName("FormLabel")
        vol_label.setAlignment(Qt.AlignCenter)

        vol_ctrl = QHBoxLayout()
        vol_ctrl.setSpacing(0)

        vol_down = QPushButton("▼")
        vol_down.setObjectName("StitchedBtnLeft")
        vol_down.setFixedSize(26, 30)

        self.volume_input = QDoubleSpinBox()
        self.volume_input.setObjectName("StitchedInput")
        self.volume_input.setDecimals(2)
        self.volume_input.setMinimum(0.01)
        self.volume_input.setMaximum(100.0)
        self.volume_input.setSingleStep(0.01)
        self.volume_input.setValue(default_lot)
        self.volume_input.setAlignment(Qt.AlignCenter)
        self.volume_input.setFixedHeight(30)

        vol_up = QPushButton("▲")
        vol_up.setObjectName("StitchedBtnRight")
        vol_up.setFixedSize(26, 30)

        vol_down.clicked.connect(lambda: self.volume_input.setValue(
            max(0.01, self.volume_input.value() - 0.01)))
        vol_up.clicked.connect(lambda: self.volume_input.setValue(
            min(100.0, self.volume_input.value() + 0.01)))

        vol_ctrl.addWidget(vol_down)
        vol_ctrl.addWidget(self.volume_input)
        vol_ctrl.addWidget(vol_up)

        vol_col.addWidget(vol_label)
        vol_col.addLayout(vol_ctrl)

        # — Contract Value column —
        cv_col = self._info_col("Contract Value", "≈1000.00 USD")

        # — Margin column —
        mg_col = self._info_col("Margin", "≈ 11.69040")

        row.addLayout(vol_col, 5)
        row.addLayout(cv_col,  5)
        row.addLayout(mg_col,  4)
        return row

    # ── Row 2: Stop Loss | gap | Take Profit ────────────────────────────
    def _create_sl_tp_row(self):
        row = QHBoxLayout()
        row.setSpacing(0)

        # — Stop Loss —
        sl_wrap = QWidget()
        sl_wrap.setFixedWidth(185)
        sl_ctrl = QHBoxLayout(sl_wrap)
        sl_ctrl.setSpacing(0)
        sl_ctrl.setContentsMargins(0, 0, 0, 0)

        sl_down = QPushButton("▼")
        sl_down.setObjectName("StitchedBtnLeft")
        sl_down.setFixedSize(26, 30)

        self.stop_loss_input = PlaceholderSpinBox("Stop Loss")
        self.stop_loss_input.setObjectName("StitchedInput")
        self.stop_loss_input.setDecimals(5)
        self.stop_loss_input.setMinimum(0.0)
        self.stop_loss_input.setMaximum(999999.0)
        self.stop_loss_input.setSingleStep(0.0001)
        self.stop_loss_input.setValue(0.0)
        self.stop_loss_input.setAlignment(Qt.AlignCenter)
        self.stop_loss_input.setFixedHeight(30)

        sl_up = QPushButton("▲")
        sl_up.setObjectName("StitchedBtnRight")
        sl_up.setFixedSize(26, 30)

        sl_down.clicked.connect(lambda: self.stop_loss_input.setValue(
            max(0.0, self.stop_loss_input.value() - 0.0001)))
        sl_up.clicked.connect(lambda: self.stop_loss_input.setValue(
            min(999999.0, self.stop_loss_input.value() + 0.0001)))

        sl_ctrl.addWidget(sl_down)
        sl_ctrl.addWidget(self.stop_loss_input)
        sl_ctrl.addWidget(sl_up)

        # — Take Profit —
        tp_wrap = QWidget()
        tp_wrap.setFixedWidth(185)
        tp_ctrl = QHBoxLayout(tp_wrap)
        tp_ctrl.setSpacing(0)
        tp_ctrl.setContentsMargins(0, 0, 0, 0)

        tp_down = QPushButton("▼")
        tp_down.setObjectName("StitchedBtnLeft")
        tp_down.setFixedSize(26, 30)

        self.take_profit_input = PlaceholderSpinBox("Take Profit")
        self.take_profit_input.setObjectName("StitchedInput")
        self.take_profit_input.setDecimals(5)
        self.take_profit_input.setMinimum(0.0)
        self.take_profit_input.setMaximum(999999.0)
        self.take_profit_input.setSingleStep(0.0001)
        self.take_profit_input.setValue(0.0)
        self.take_profit_input.setAlignment(Qt.AlignCenter)
        self.take_profit_input.setFixedHeight(30)

        tp_up = QPushButton("▲")
        tp_up.setObjectName("StitchedBtnRight")
        tp_up.setFixedSize(26, 30)

        tp_down.clicked.connect(lambda: self.take_profit_input.setValue(
            max(0.0, self.take_profit_input.value() - 0.0001)))
        tp_up.clicked.connect(lambda: self.take_profit_input.setValue(
            min(999999.0, self.take_profit_input.value() + 0.0001)))

        tp_ctrl.addWidget(tp_down)
        tp_ctrl.addWidget(self.take_profit_input)
        tp_ctrl.addWidget(tp_up)

        row.addWidget(sl_wrap)
        row.addStretch()
        row.addWidget(tp_wrap)
        return row

    # ── Row 3: Sell | Buy ────────────────────────────────────────────────
    def _create_buttons_row(self):
        row = QHBoxLayout()
        row.setSpacing(8)

        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        self.sell_btn.setFixedHeight(52)
        self.sell_btn.setStyleSheet(
            BUTTON_STYLES['sell'] + " font-size: 13px; font-weight: bold;")
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))

        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        self.buy_btn.setFixedHeight(52)
        self.buy_btn.setStyleSheet(
            BUTTON_STYLES['buy'] + " font-size: 13px; font-weight: bold;")
        self.buy_btn.clicked.connect(lambda: self._submit_order("BUY"))

        row.addWidget(self.sell_btn)
        row.addWidget(self.buy_btn)
        return row

    # ── Remarks ──────────────────────────────────────────────────────────
    def _create_remarks_section(self):
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        self.remarks_input.setFixedHeight(48)
        return self.remarks_input

    # ── Info strip ───────────────────────────────────────────────────────
    def _create_info_row(self):
        row = QHBoxLayout()
        row.setSpacing(0)
        row.setContentsMargins(0, 2, 0, 0)

        info_items = [
            ("Spread",         "0.00019"),
            ("Commission",     "4"),
            ("Pip Value",      "10"),
            ("Daily Swap USD", "Sell: -2.79  Buy: -3.15"),
        ]
        for i, (lbl, val) in enumerate(info_items):
            col = QVBoxLayout()
            col.setSpacing(1)
            l = QLabel(lbl); l.setObjectName("InfoLabel"); l.setAlignment(Qt.AlignCenter)
            v = QLabel(val); v.setObjectName("InfoValue"); v.setAlignment(Qt.AlignCenter)
            col.addWidget(l); col.addWidget(v)
            row.addLayout(col)
            if i < len(info_items) - 1:
                row.addStretch(1)
        return row

    # ── Helper: label + readonly value box column ─────────────────────────
    def _info_col(self, label_text, value_text):
        col = QVBoxLayout()
        col.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setObjectName("FormLabel")
        lbl.setAlignment(Qt.AlignCenter)

        val = QLabel(value_text)
        val.setObjectName("FormValue")
        val.setAlignment(Qt.AlignCenter)
        val.setFixedHeight(30)

        col.addWidget(lbl)
        col.addWidget(val)
        return col

    # ------------------------------------------------------------------ #
    # Business logic (unchanged)
    # ------------------------------------------------------------------ #
    def _submit_order(self, order_type):
        order_data = {
            'symbol':         self.symbol,
            'type':           order_type,
            'volume':         self.volume_input.value(),
            'stop_loss':      self.stop_loss_input.value() if self.stop_loss_input.value() > 0 else None,
            'take_profit':    self.take_profit_input.value() if self.take_profit_input.value() > 0 else None,
            'remarks':        self.remarks_input.toPlainText(),
            'order_category': 'market'
        }
        LOG.info("MarketOrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)

    def update_prices(self, sell_price, buy_price):
        self.sell_price = sell_price
        self.buy_price  = buy_price
        self.sell_btn.setText(f"{sell_price}\nSell")
        self.buy_btn.setText(f"{buy_price}\nBuy")
        LOG.debug("MarketOrderForm prices: %s / %s", sell_price, buy_price)