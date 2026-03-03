"""
Market Order Form Component - Form for placing market orders
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.ui.components.volume_control import VolumeControl
from MarketWatch_jetfyx.ui.components.numeric_input import NumericInput
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES
import logging

LOG = logging.getLogger(__name__)


class MarketOrderForm(QWidget):
    """Reusable market order form component"""

    orderSubmitted = Signal(dict)  # Emits order data

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, parent=None):
        super().__init__(parent)

        self.symbol     = symbol
        self.sell_price = sell_price
        self.buy_price  = buy_price

        self.setup_ui(default_lot)
        self._apply_theme()

        # Subscribe to dynamic theme changes
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # Theme
    # ──────────────────────────────────────────────────────────────
    def _apply_theme(self):
        """Apply dynamic theme colors instead of hardcoded hex values"""
        try:
            from Theme.theme_manager import ThemeManager
            tok      = ThemeManager.instance().tokens()
            bg_input = tok.get("bg_input",      "#f5f5f5")
            text_pri = tok.get("text_primary",  "#1a202c")
            text_sec = tok.get("text_secondary","#6b7280")
            border   = tok.get("border_primary","#e5e7eb")
            is_dark  = tok.get("is_dark", "false") == "true"
        except Exception:
            bg_input, text_pri, text_sec, border, is_dark = (
                "#f5f5f5", "#1a202c", "#6b7280", "#e5e7eb", False
            )

        if is_dark:
            if border   == "#e5e7eb": border   = "#374151"
            if bg_input == "#f5f5f5": bg_input = "#1f2937"

        self.setStyleSheet(f"""
            QWidget {{ background: transparent; }}

            QLabel#FormLabel {{
                font-weight: 600;
                font-size: 10px;
                color: {text_sec};
                letter-spacing: 0.5px;
                text-transform: uppercase;
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
                padding: 2px 6px;
            }}

            QFrame#Separator {{
                color: {border};
                background-color: {border};
                max-height: 1px;
                border: none;
            }}

            QLabel#InfoLabel {{
                font-size: 9px;
                color: {text_sec};
                letter-spacing: 0.3px;
            }}
            QLabel#InfoValue {{
                font-size: 10px;
                color: {text_pri};
                font-weight: 600;
            }}
        """)

    # ──────────────────────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────────────────────
    def setup_ui(self, default_lot):
        """Setup the form UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 6, 8, 6)

        layout.addLayout(self._create_top_row(default_lot))
        layout.addLayout(self._create_sl_tp_row())
        layout.addLayout(self._create_buttons_row())
        layout.addSpacing(8)   # gap between buttons and remarks
        layout.addWidget(self._create_remarks_section())
        layout.addSpacing(4)
        layout.addWidget(self._make_separator())
        layout.addSpacing(4)
        layout.addLayout(self._create_info_row())
        layout.addStretch()  # push all content to top, no gap

    def _make_separator(self):
        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        return sep

    # ── Rows ────────────────────────────────────────────────────
    def _create_top_row(self, default_lot):
        """Volume | Contract Value | Margin"""
        row = QHBoxLayout()
        row.setSpacing(8)

        self.volume_control = VolumeControl(default_lot)

        row.addWidget(self.volume_control)
        row.addLayout(self._create_info_field("Contract Value", "≈1000.00 USD"))
        row.addLayout(self._create_info_field("Margin", "≈ 11.69040"))
        return row

    def _create_sl_tp_row(self):
        """Stop Loss | Take Profit"""
        row = QHBoxLayout()
        row.setSpacing(8)

        self.stop_loss_input = NumericInput(
            label_text="", placeholder="Stop Loss",
            default_value=0.0, decimals=5
        )
        self.take_profit_input = NumericInput(
            label_text="", placeholder="Take Profit",
            default_value=0.0, decimals=5
        )

        row.addWidget(self.stop_loss_input)
        row.addWidget(self.take_profit_input)
        return row

    def _create_buttons_row(self):
        """Sell | Buy action buttons"""
        row = QHBoxLayout()
        row.setSpacing(8)

        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        self.sell_btn.setFixedHeight(52)
        self.sell_btn.setStyleSheet(BUTTON_STYLES['sell'])
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))

        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        self.buy_btn.setFixedHeight(52)
        self.buy_btn.setStyleSheet(BUTTON_STYLES['buy'])
        self.buy_btn.clicked.connect(lambda: self._submit_order("BUY"))

        row.addWidget(self.sell_btn)
        row.addWidget(self.buy_btn)
        return row

    def _create_remarks_section(self):
        """Compact remarks text field — placeholder only, no label"""
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        self.remarks_input.setFixedHeight(52)
        return self.remarks_input

    def _create_info_row(self):
        """Bottom strip: Spread | Commission | Pip Value | Daily Swap"""
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

            label = QLabel(lbl)
            label.setObjectName("InfoLabel")
            label.setAlignment(Qt.AlignCenter)

            value = QLabel(val)
            value.setObjectName("InfoValue")
            value.setAlignment(Qt.AlignCenter)

            col.addWidget(label)
            col.addWidget(value)
            row.addLayout(col)

            if i < len(info_items) - 1:
                row.addStretch(1)

        return row

    # ── Helpers ─────────────────────────────────────────────────
    def _create_info_field(self, label_text, value_text):
        """Labeled static display field"""
        container = QVBoxLayout()
        container.setSpacing(3)

        label = QLabel(label_text)
        label.setObjectName("FormLabel")

        value = QLabel(value_text)
        value.setObjectName("FormValue")
        value.setAlignment(Qt.AlignCenter)
        value.setFixedHeight(26)

        container.addWidget(label)
        container.addWidget(value)
        return container

    # ── Business logic (unchanged) ───────────────────────────────
    def _submit_order(self, order_type):
        """Submit market order"""
        order_data = {
            'symbol':         self.symbol,
            'type':           order_type,
            'volume':         self.volume_control.get_volume(),
            'stop_loss':      self.stop_loss_input.get_value() if self.stop_loss_input.get_text() else None,
            'take_profit':    self.take_profit_input.get_value() if self.take_profit_input.get_text() else None,
            'remarks':        self.remarks_input.toPlainText(),
            'order_category': 'market'
        }
        LOG.info("MarketOrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)

    def update_prices(self, sell_price, buy_price):
        """Update displayed prices"""
        self.sell_price = sell_price
        self.buy_price  = buy_price
        self.sell_btn.setText(f"{sell_price}\nSell")
        self.buy_btn.setText(f"{buy_price}\nBuy")
        LOG.debug("MarketOrderForm update_prices: %s %s", sell_price, buy_price)