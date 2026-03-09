"""
Limit Order Form Component - same styling as MarketOrderForm
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QTextEdit, QFrame,
    QCheckBox, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES
import logging

LOG = logging.getLogger(__name__)


# ── TickCheckBox — draws a real white tick when checked ──────────────────
class TickCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.isChecked():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        ih = 14
        iy = (self.height() - ih) // 2
        ix = 0
        pen = QPen(QColor("#ffffff"), 2.0)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawLine(ix + 2,  iy + 7,  ix + 5,  iy + 10)
        p.drawLine(ix + 5,  iy + 10, ix + 11, iy + 4)
        p.end()


# ── Helpers (identical to market_order_form) ─────────────────────────────
def _detect_dark() -> bool:
    from PySide6.QtGui import QColor
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()

        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool):
                return val
            s = str(val).lower()
            if s in ("true", "1", "yes", "dark"):   return True
            if s in ("false", "0", "no", "light"):  return False

        for key in ("bg_panel", "background", "bg_primary", "bg_base", "bg"):
            cs = tok.get(key, None)
            if cs:
                c = QColor(cs)
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


# ── LimitOrderForm ────────────────────────────────────────────────────────
class LimitOrderForm(QWidget):

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
    # Theme — identical palette to MarketOrderForm
    # ------------------------------------------------------------------ #
    def _apply_theme(self):
        dark   = _detect_dark()
        accent = _accent()

        if dark:
            bg_input    = "#1e2a3a"
            text_pri    = "#e2e8f0"
            text_sec    = "#94a3b8"
            border      = "#2d3a4a"
            arrow_bg    = "#253347"
            arrow_color = "#cbd5e1"
        else:
            bg_input    = "#f9fafb"
            text_pri    = "#111827"
            text_sec    = "#6b7280"
            border      = "#e2e8f0"
            arrow_bg    = "#f3f4f6"
            arrow_color = "#374151"

        self.setStyleSheet(f"""
            LimitOrderForm {{ background: transparent; }}
            QWidget         {{ background: transparent; }}

            QLabel#FormLabel {{
                font-size: 9px; font-weight: 700;
                color: {text_sec};
                letter-spacing: 0.8px;
                background: transparent;
            }}

            QLabel#FormValue {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 5px;
                font-size: 11px;
                color: {text_pri};
                padding: 2px 6px;
            }}

            QTextEdit {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 5px;
                font-size: 11px;
                color: {text_pri};
                padding: 4px 6px;
            }}
            QTextEdit:focus {{ border: 1px solid {accent}; }}

            QCheckBox {{
                font-size: 11px;
                color: {text_sec};
                font-weight: 500;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 1px solid {border};
                border-radius: 3px;
                background: {bg_input};
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border-color: {accent};
            }}

            QPushButton#StitchedBtnLeft,
            QPushButton#StitchedBtnRight {{
                background-color: {arrow_bg};
                border: 1px solid {border};
                color: {arrow_color};
                font-size: 10px; font-weight: 700;
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

            QDoubleSpinBox#StitchedInput {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 0px;
                color: {text_pri};
                font-size: 12px; font-weight: 600;
            }}
            QDoubleSpinBox#StitchedInput:focus {{
                border-top: 1px solid {accent};
                border-bottom: 1px solid {accent};
            }}
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {{
                width: 0px; border: none; background: transparent;
            }}

            QFrame#Separator {{
                background-color: {border};
                max-height: 1px; border: none;
            }}

            QLabel#InfoLabel {{
                font-size: 9px; color: {text_sec};
                letter-spacing: 0.3px; background: transparent;
            }}
            QLabel#InfoValue {{
                font-size: 10px; color: {text_pri};
                font-weight: 600; background: transparent;
            }}

            QLabel#SellPriceLabel {{
                font-size: 13px; font-weight: 700;
                color: #ef4444;
                background: transparent;
            }}
            QLabel#BuyPriceLabel {{
                font-size: 13px; font-weight: 700;
                color: #22c55e;
                background: transparent;
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
        layout.addSpacing(10)
        layout.addLayout(self._create_price_row())
        layout.addSpacing(6)
        layout.addLayout(self._create_expiration_row())
        layout.addSpacing(10)
        layout.addLayout(self._create_price_display_row())
        layout.addSpacing(6)
        layout.addLayout(self._create_buttons_row())
        layout.addSpacing(8)
        layout.addWidget(self._create_remarks_section())
        layout.addSpacing(6)
        layout.addWidget(self._make_separator())
        layout.addSpacing(6)
        layout.addLayout(self._create_info_row())

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

        # — Volume —
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

        row.addLayout(vol_col, 5)
        row.addLayout(self._info_col("Contract Value", "≈1000.00 USD"), 5)
        row.addLayout(self._info_col("Margin", "≈ 11.68880"), 4)
        return row

    # ── Row 2: Stop Loss | Entry Price | Take Profit (with labels above) ──
    def _create_price_row(self):
        row = QHBoxLayout()
        row.setSpacing(8)

        def _labeled_spin(label_text, placeholder, init_val=0.0):
            """Returns (col_layout, spinbox)"""
            col = QVBoxLayout()
            col.setSpacing(3)

            lbl = QLabel(label_text)
            lbl.setObjectName("FormLabel")
            lbl.setAlignment(Qt.AlignCenter)

            wrap = QWidget()
            ctrl = QHBoxLayout(wrap)
            ctrl.setSpacing(0)
            ctrl.setContentsMargins(0, 0, 0, 0)

            btn_down = QPushButton("▼")
            btn_down.setObjectName("StitchedBtnLeft")
            btn_down.setFixedSize(24, 30)

            spin = PlaceholderSpinBox(placeholder)
            spin.setObjectName("StitchedInput")
            spin.setDecimals(5)
            spin.setMinimum(0.0)
            spin.setMaximum(999999.0)
            spin.setSingleStep(0.0001)
            spin.setValue(init_val)
            spin.setAlignment(Qt.AlignCenter)
            spin.setFixedHeight(30)

            btn_up = QPushButton("▲")
            btn_up.setObjectName("StitchedBtnRight")
            btn_up.setFixedSize(24, 30)

            btn_down.clicked.connect(lambda: spin.setValue(max(0.0, spin.value() - 0.0001)))
            btn_up.clicked.connect(lambda: spin.setValue(min(999999.0, spin.value() + 0.0001)))

            ctrl.addWidget(btn_down)
            ctrl.addWidget(spin)
            ctrl.addWidget(btn_up)

            col.addWidget(lbl)
            col.addWidget(wrap)
            return col, spin

        init_ep = float(self.sell_price) if self.sell_price else 0.0
        sl_col, self.stop_loss_input   = _labeled_spin("Stop Loss",   "Stop Loss")
        ep_col, self.entry_price_input = _labeled_spin("Entry Price",  "Entry Price", init_ep)
        tp_col, self.take_profit_input = _labeled_spin("Take Profit",  "Take Profit")

        row.addLayout(sl_col)
        row.addLayout(ep_col)
        row.addLayout(tp_col)
        return row

    # ── Row 3: Expiration checkbox — label LEFT, box RIGHT ───────────────
    def _create_expiration_row(self):
        row = QHBoxLayout()
        row.setSpacing(0)
        row.setContentsMargins(0, 0, 0, 0)

        # Put checkbox on left of label using custom layout
        self.expiration_checkbox = TickCheckBox("")
        self.expiration_checkbox.setFixedSize(16, 16)

        exp_label = QLabel("Expiration Date & Time")
        exp_label.setObjectName("FormLabel")
        exp_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        row.addStretch()
        row.addWidget(exp_label)
        row.addSpacing(6)
        row.addWidget(self.expiration_checkbox)
        row.addStretch()
        return row

    # ── Price display row: sell price (red) | buy price (green) ─────────
    def _create_price_display_row(self):
        row = QHBoxLayout()
        row.setSpacing(8)

        self.sell_price_lbl = QLabel(str(self.sell_price))
        self.sell_price_lbl.setObjectName("SellPriceLabel")
        self.sell_price_lbl.setAlignment(Qt.AlignCenter)

        self.buy_price_lbl = QLabel(str(self.buy_price))
        self.buy_price_lbl.setObjectName("BuyPriceLabel")
        self.buy_price_lbl.setAlignment(Qt.AlignCenter)

        row.addWidget(self.sell_price_lbl)
        row.addWidget(self.buy_price_lbl)
        return row

    # ── Row 5: Sell Limit | Buy Stop (text only, price shown above) ──────
    def _create_buttons_row(self):
        row = QHBoxLayout()
        row.setSpacing(8)

        self.sell_limit_btn = QPushButton("Sell Limit")
        self.sell_limit_btn.setFixedHeight(44)
        self.sell_limit_btn.setStyleSheet(
            BUTTON_STYLES['sell'] + " font-size: 14px; font-weight: bold;")
        self.sell_limit_btn.clicked.connect(lambda: self._submit_order("SELL_LIMIT"))

        self.buy_stop_btn = QPushButton("Buy Stop")
        self.buy_stop_btn.setFixedHeight(44)
        self.buy_stop_btn.setStyleSheet(
            BUTTON_STYLES['buy'] + " font-size: 14px; font-weight: bold;")
        self.buy_stop_btn.clicked.connect(lambda: self._submit_order("BUY_STOP"))

        row.addWidget(self.sell_limit_btn)
        row.addWidget(self.buy_stop_btn)
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
            ("Spread",         "0.00014"),
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

    # ── Helper: centered label + readonly value box ───────────────────────
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
            'entry_price':    self.entry_price_input.value() if self.entry_price_input.value() > 0 else None,
            'stop_loss':      self.stop_loss_input.value() if self.stop_loss_input.value() > 0 else None,
            'take_profit':    self.take_profit_input.value() if self.take_profit_input.value() > 0 else None,
            'remarks':        self.remarks_input.toPlainText(),
            'has_expiration': self.expiration_checkbox.isChecked(),
            'order_category': 'limit'
        }
        LOG.info("LimitOrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)

    def update_prices(self, sell_price, buy_price, hub_received_timestamp=None):
        import time
        self.sell_price = sell_price
        self.buy_price  = buy_price
        # Update price display labels
        try:
            self.sell_price_lbl.setText(str(sell_price))
            self.buy_price_lbl.setText(str(buy_price))
        except Exception:
            pass
        # Update entry price if still at default
        if self.entry_price_input.value() == 0.0:
            self.entry_price_input.setValue(float(sell_price) if sell_price else 0.0)
        if hub_received_timestamp:
            latency = (time.time() - hub_received_timestamp) * 1000
            LOG.debug("[Latency] LimitOrderForm: %s latency=%.2fms", self.symbol, latency)