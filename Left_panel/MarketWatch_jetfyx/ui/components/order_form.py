"""
Order Form Component - Reusable order form widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES
import logging

LOG = logging.getLogger(__name__)


class OrderForm(QWidget):
    """Reusable order form component"""

    orderSubmitted = Signal(dict)  # Emits order data

    def __init__(self, symbol, sell_price, buy_price, default_lot=0.01, parent=None):
        super().__init__(parent)

        self.symbol     = symbol
        self.sell_price = sell_price
        self.buy_price  = buy_price

        self.setup_ui(default_lot)
        self._apply_theme()

        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # Theme
    # ──────────────────────────────────────────────────────────────
    def _apply_theme(self):
        """Apply dynamic theme colors"""
        try:
            from Theme.theme_manager import ThemeManager
            tok      = ThemeManager.instance().tokens()
            bg_input = tok.get("bg_input",        "#f5f5f5")
            text_pri = tok.get("text_primary",     "#1a202c")
            text_sec = tok.get("text_secondary",   "#6b7280")
            border   = tok.get("border_primary",   "#e5e7eb")
            bg_hover = tok.get("bg_button_hover",  "#e2e8f0")
            accent   = tok.get("accent",           "#1976d2") 
            is_dark  = tok.get("is_dark", "false") == "true"
        except Exception:
            bg_input, text_pri, text_sec, border, bg_hover, accent, is_dark = (
                "#f5f5f5", "#1a202c", "#6b7280", "#e5e7eb", "#e2e8f0", "#1976d2", False
            )

        if is_dark:
            if border   == "#e5e7eb": border   = "#374151"
            if bg_input == "#f5f5f5": bg_input = "#1f2937"
            if bg_hover == "#e2e8f0": bg_hover = "#4a5568"

        self.setStyleSheet(f"""
            OrderForm {{ background: transparent; }}

            QLabel#FormLabel {{
                font-weight: 600;
                font-size: 10px;
                color: {text_sec};
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }}

            QTextEdit {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 5px;
                color: {text_pri};
                font-size: 11px;
                padding: 2px 6px;
            }}
            QTextEdit:focus {{
                border: 1px solid {accent};
                outline: none;
            }}

            /* 🟢 FIX: Use Segoe UI Symbol and 12px size so arrows fit perfectly */
            QPushButton#StitchedBtnLeft, QPushButton#StitchedBtnRight {{
                background-color: {bg_hover};
                border: 1px solid {border};
                color: {text_pri};
                font-family: "Segoe UI Symbol", Arial, sans-serif;
                font-size: 12px;
                padding: 0px; 
                margin: 0px;
            }}
            QPushButton#StitchedBtnLeft:hover, QPushButton#StitchedBtnRight:hover {{
                background-color: {border};
            }}
            QPushButton#StitchedBtnLeft {{
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-right: none; 
            }}
            QPushButton#StitchedBtnRight {{
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border-left: none; 
            }}

            QDoubleSpinBox#StitchedInput {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 0px;
                color: {text_pri};
                font-size: 12px;
                font-weight: bold;
            }}
            QDoubleSpinBox#StitchedInput:focus {{
                border-top: 1px solid {accent};
                border-bottom: 1px solid {accent};
                outline: none;
            }}
            
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 0px;
                background: transparent;
                border: none;
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

        layout.addSpacing(4)
        layout.addLayout(self._create_volume_row(default_lot))
        layout.addLayout(self._create_sl_tp_row())
        layout.addSpacing(4)
        layout.addLayout(self._create_buttons_row())
        layout.addSpacing(8)
        layout.addWidget(self._create_remarks_section())
        layout.addSpacing(4)
        layout.addWidget(self._make_separator())
        layout.addSpacing(4)
        layout.addLayout(self._create_info_row())
        
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _make_separator(self):
        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        return sep

    # ── Rows ────────────────────────────────────────────────────
    def _create_volume_row(self, default_lot):
        """Volume control row"""
        row = QHBoxLayout()
        row.setSpacing(8)

        vol_col = QVBoxLayout()
        vol_col.setSpacing(3)

        vol_label = QLabel("Volume")
        vol_label.setObjectName("FormLabel")

        vol_ctrl = QHBoxLayout()
        vol_ctrl.setSpacing(0)

        # 🟢 FIX: Restored Down Arrow
        vol_down = QPushButton("▼")
        vol_down.setObjectName("StitchedBtnLeft")
        vol_down.setFixedSize(28, 28)

        self.volume_input = QDoubleSpinBox()
        self.volume_input.setObjectName("StitchedInput")
        self.volume_input.setDecimals(2)
        self.volume_input.setMinimum(0.01)
        self.volume_input.setMaximum(100.0)
        self.volume_input.setSingleStep(0.01)
        self.volume_input.setValue(default_lot)
        self.volume_input.setAlignment(Qt.AlignCenter)
        self.volume_input.setFixedHeight(28)

        # 🟢 FIX: Restored Up Arrow
        vol_up = QPushButton("▲")
        vol_up.setObjectName("StitchedBtnRight")
        vol_up.setFixedSize(28, 28)

        vol_down.clicked.connect(
            lambda: self.volume_input.setValue(max(0.01, self.volume_input.value() - 0.01))
        )
        vol_up.clicked.connect(
            lambda: self.volume_input.setValue(min(100.0, self.volume_input.value() + 0.01))
        )

        vol_ctrl.addWidget(vol_down)
        vol_ctrl.addWidget(self.volume_input)
        vol_ctrl.addWidget(vol_up)

        vol_col.addWidget(vol_label)
        vol_col.addLayout(vol_ctrl)

        row.addLayout(vol_col)
        return row

    def _create_sl_tp_row(self):
        """Stop Loss | Take Profit"""
        row = QHBoxLayout()
        row.setSpacing(8)

        sl_ctrl = QHBoxLayout()
        sl_ctrl.setSpacing(0)
        
        # 🟢 FIX: Restored Down Arrow
        sl_down = QPushButton("▼")
        sl_down.setObjectName("StitchedBtnLeft")
        sl_down.setFixedSize(28, 28)
        
        self.sl_input = QDoubleSpinBox()
        self.sl_input.setObjectName("StitchedInput")
        self.sl_input.setDecimals(5)
        self.sl_input.setMinimum(0.0)
        self.sl_input.setMaximum(999999.0)
        self.sl_input.setSingleStep(0.0001)
        self.sl_input.setValue(0.0)
        self.sl_input.setSpecialValueText("Stop Loss")
        self.sl_input.setAlignment(Qt.AlignCenter)
        self.sl_input.setFixedHeight(28)
        
        # 🟢 FIX: Restored Up Arrow
        sl_up = QPushButton("▲")
        sl_up.setObjectName("StitchedBtnRight")
        sl_up.setFixedSize(28, 28)
        
        sl_down.clicked.connect(lambda: self.sl_input.setValue(max(0.0, self.sl_input.value() - 0.0001)))
        sl_up.clicked.connect(lambda: self.sl_input.setValue(min(999999.0, self.sl_input.value() + 0.0001)))
        
        sl_ctrl.addWidget(sl_down)
        sl_ctrl.addWidget(self.sl_input)
        sl_ctrl.addWidget(sl_up)

        tp_ctrl = QHBoxLayout()
        tp_ctrl.setSpacing(0)
        
        # 🟢 FIX: Restored Down Arrow
        tp_down = QPushButton("▼")
        tp_down.setObjectName("StitchedBtnLeft")
        tp_down.setFixedSize(28, 28)
        
        self.tp_input = QDoubleSpinBox()
        self.tp_input.setObjectName("StitchedInput")
        self.tp_input.setDecimals(5)
        self.tp_input.setMinimum(0.0)
        self.tp_input.setMaximum(999999.0)
        self.tp_input.setSingleStep(0.0001)
        self.tp_input.setValue(0.0)
        self.tp_input.setSpecialValueText("Take Profit")
        self.tp_input.setAlignment(Qt.AlignCenter)
        self.tp_input.setFixedHeight(28)
        
        # 🟢 FIX: Restored Up Arrow
        tp_up = QPushButton("▲")
        tp_up.setObjectName("StitchedBtnRight")
        tp_up.setFixedSize(28, 28)
        
        tp_down.clicked.connect(lambda: self.tp_input.setValue(max(0.0, self.tp_input.value() - 0.0001)))
        tp_up.clicked.connect(lambda: self.tp_input.setValue(min(999999.0, self.tp_input.value() + 0.0001)))
        
        tp_ctrl.addWidget(tp_down)
        tp_ctrl.addWidget(self.tp_input)
        tp_ctrl.addWidget(tp_up)

        row.addLayout(sl_ctrl)
        row.addLayout(tp_ctrl)
        return row

    def _create_buttons_row(self):
        """Sell | Buy action buttons"""
        row = QHBoxLayout()
        row.setSpacing(8)

        self.sell_btn = QPushButton(f"{self.sell_price}\nSell")
        self.sell_btn.setFixedHeight(52)
        self.sell_btn.setStyleSheet(BUTTON_STYLES['sell'] + " font-size: 13px; font-weight: bold;")
        self.sell_btn.clicked.connect(lambda: self._submit_order("SELL"))

        self.buy_btn = QPushButton(f"{self.buy_price}\nBuy")
        self.buy_btn.setFixedHeight(52)
        self.buy_btn.setStyleSheet(BUTTON_STYLES['buy'] + " font-size: 13px; font-weight: bold;")
        self.buy_btn.clicked.connect(lambda: self._submit_order("BUY"))

        row.addWidget(self.sell_btn)
        row.addWidget(self.buy_btn)
        return row

    def _create_remarks_section(self):
        """Compact remarks field"""
        self.remarks_input = QTextEdit()
        self.remarks_input.setPlaceholderText("Remarks")
        self.remarks_input.setFixedHeight(48)
        return self.remarks_input

    def _create_info_row(self):
        """Bottom strip: Spread | Commission | Pip Value | Daily Swap"""
        row = QHBoxLayout()
        row.setSpacing(0)
        row.setContentsMargins(0, 2, 0, 0)

        info_labels = [
            ("Spread",         "0.00"),
            ("Commission",     "0"),
            ("Pip Value",      "1"),
            ("Daily Swap USD", "Sell:  Buy:"),
        ]

        for i, (lbl, val) in enumerate(info_labels):
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

            if i < len(info_labels) - 1:
                row.addStretch(1)

        return row

    # ── Business logic (unchanged) ───────────────────────────────
    def _submit_order(self, order_type):
        """Submit order"""
        order_data = {
            'symbol':     self.symbol,
            'type':       order_type,
            'volume':     self.volume_input.value(),
            'stop_loss':  self.sl_input.value() if self.sl_input.value() > 0 else None,
            'take_profit':self.tp_input.value() if self.tp_input.value() > 0 else None,
            'remarks':    self.remarks_input.toPlainText()
        }
        LOG.info("OrderForm submit: %s", order_data)
        self.orderSubmitted.emit(order_data)

    def update_prices(self, sell_price, buy_price, hub_received_timestamp=None):
        """Update displayed prices. Log latency if timestamp is provided."""
        import time
        self.sell_price = sell_price
        self.buy_price  = buy_price
        self.sell_btn.setText(f"{sell_price}\nSell")
        self.buy_btn.setText(f"{buy_price}\nBuy")
        if hub_received_timestamp:
            latency = (time.time() - hub_received_timestamp) * 1000  # ms
            LOG.debug("[Latency] OrderForm Buttons: %s latency = %.2f ms", self.symbol, latency)