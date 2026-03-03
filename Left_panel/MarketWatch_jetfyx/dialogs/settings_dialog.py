"""
Settings Dialog - Application settings configuration
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QColor, QPalette, QFont, QPainter
from MarketWatch_jetfyx.widgets.toggle_switch import ToggleSwitch

try:
    from Theme.theme_manager import ThemeManager as _ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _ThemeManager = None
    _THEME_AVAILABLE = False


def _set_title_bar_dark(win_id, dark: bool):
    """
    Ask Windows DWM to render the native title bar in dark / light mode.
    No-op on non-Windows or if ctypes is unavailable.
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 20H1+ / Windows 11)
    """
    try:
        import ctypes
        import ctypes.wintypes
        value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(win_id),
            20,                          # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass  # Non-Windows or older Windows — silently skip


class _IconButton(QPushButton):
    """QPushButton that paints its label with QPainter — immune to Windows color overrides."""
    def __init__(self, text, color="#4a5568", parent=None):
        super().__init__(text, parent)
        self._icon_color = color

    def paintEvent(self, event):
        # Draw the button background via the normal style
        from PySide6.QtWidgets import QStyleOptionButton, QStyle
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_PushButtonBevel, opt, painter, self)

        # Draw our text on top with guaranteed color
        painter.setPen(QColor(self._icon_color))
        font = QFont("Segoe UI Symbol", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), 0x0004 | 0x0080, self.text())  # AlignHCenter | AlignVCenter
        painter.end()



class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""

    settingsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setFixedSize(350, 180)

        self.settings = {
            'advance_view': False,
            'one_click_trade': False,
            'default_lot': 0.01,
            'default_lot_enabled': False
        }

        self._setup_ui()
        self.apply_theme()

        # Re-apply whenever the active theme changes (live updates while open)
        if _THEME_AVAILABLE:
            try:
                _ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Theme helpers
    # ------------------------------------------------------------------
    def _tokens(self) -> dict:
        """Return current theme tokens, falling back to empty dict."""
        if _THEME_AVAILABLE:
            try:
                return _ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    def _is_dark(self) -> bool:
        """True when the active theme has a dark background."""
        t = self._tokens()
        bg = t.get("bg_popup", "#ffffff").lstrip("#")
        try:
            r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            return (r * 299 + g * 587 + b * 114) / 1000 < 128
        except Exception:
            return False

    def apply_theme(self):
        """
        Re-style every widget from the active theme tokens.
        Called on construction AND whenever theme_changed fires.
        """
        t = self._tokens()

        bg       = t.get("bg_popup",        "#ffffff")
        text_p   = t.get("text_primary",    "#1a202c")
        text_s   = t.get("text_secondary",  "#4a5568")
        text_m   = t.get("text_muted",      "#9ca3af")
        bg_inp   = t.get("bg_input",        "#f5f7fa")
        border   = t.get("border_primary",  "#e5e7eb")
        border_f = t.get("border_focus",    "#1976d2")
        accent   = t.get("accent",          "#1976d2")
        acc_t    = t.get("accent_text",     "#ffffff")
        bg_btn   = t.get("bg_button",       "#f0f4f8")
        bg_bth   = t.get("bg_button_hover", "#e2e8f0")
        pos      = t.get("text_positive",   "#4caf50")

        # ── Native title bar dark mode (Windows only) ─────────────────
        try:
            _set_title_bar_dark(self.winId(), self._is_dark())
        except Exception:
            pass

        # ── Dialog background ─────────────────────────────────────────
        # Use palette to force the window background — setStyleSheet alone
        # is not reliable on Windows (native frame shows through).
        try:
            pal = self.palette()
            pal.setColor(QPalette.Window, QColor(bg))
            pal.setColor(QPalette.WindowText, QColor(text_p))
            self.setPalette(pal)
            self.setAutoFillBackground(True)
        except Exception:
            pass

        # Scoped stylesheet — only targets named children, NOT QWidget blanket
        # (blanket QWidget { background: transparent } was causing black bg)
        self.setStyleSheet(f"""
            QDialog {{
                background: {bg};
            }}
            QLabel {{
                background: transparent;
                color: {text_p};
            }}
            QWidget {{
                background: {bg};
            }}
        """)

        # ── Row title labels ──────────────────────────────────────────
        for lbl in self.findChildren(QLabel, "SettingTitle"):
            lbl.setStyleSheet(
                f"font-size: 14px; font-weight: 600; "
                f"color: {text_p}; background: transparent;"
            )
        for lbl in self.findChildren(QLabel, "SettingDesc"):
            lbl.setStyleSheet(
                f"font-size: 11px; color: {text_s}; background: transparent;"
            )
        for lbl in self.findChildren(QLabel, "SettingLabel"):
            lbl.setStyleSheet(
                f"font-size: 14px; font-weight: 600; "
                f"color: {text_p}; background: transparent;"
            )

        # ── Down arrow button ─────────────────────────────────────────
        if hasattr(self, "down_arrow_btn"):
            self.down_arrow_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg_btn};
                    border: 1px solid {border};
                    border-right: none;
                    border-top-left-radius: 6px;
                    border-bottom-left-radius: 6px;
                    color: {text_s};
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {bg_bth};
                    border-color: {border_f};
                }}
                QPushButton:disabled {{
                    background: {bg_inp};
                    color: {text_m};
                    border-color: {border};
                }}
            """)

        # ── Lot input field ───────────────────────────────────────────
        if hasattr(self, "default_lot_input"):
            is_editing = hasattr(self, "edit_btn") and self.edit_btn.isChecked()
            if is_editing:
                self.default_lot_input.setStyleSheet(f"""
                    QLineEdit {{
                        padding: 6px;
                        border: 2px solid {border_f};
                        border-left: none;
                        border-right: none;
                        font-size: 13px;
                        font-weight: 600;
                        background: {bg};
                        color: {text_p};
                    }}
                """)
            else:
                self.default_lot_input.setStyleSheet(f"""
                    QLineEdit {{
                        padding: 6px;
                        border: 1px solid {border};
                        border-left: none;
                        border-right: none;
                        font-size: 13px;
                        font-weight: 600;
                        background: {bg_inp};
                        color: {text_m};
                    }}
                """)

        # ── Up arrow button ───────────────────────────────────────────
        if hasattr(self, "up_arrow_btn"):
            self.up_arrow_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg_btn};
                    border: 1px solid {border};
                    border-left: none;
                    color: {text_s};
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {bg_bth};
                    border-color: {border_f};
                }}
                QPushButton:disabled {{
                    background: {bg_inp};
                    color: {text_m};
                    border-color: {border};
                }}
            """)

        # ── Edit / confirm button ─────────────────────────────────────
        if hasattr(self, "edit_btn"):
            if self.edit_btn.isChecked():
                # Confirm / save state — positive green fill
                self.edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {pos};
                        border: 1px solid {pos};
                        border-left: none;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                        color: {acc_t};
                        font-size: 14px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: {accent};
                        border-color: {accent};
                    }}
                """)
            else:
                # View / pencil state — accent-coloured icon on muted bg
                self.edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg_btn};
                        border: 1px solid {border};
                        border-left: none;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                        color: {accent};
                        font-size: 14px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: {bg_bth};
                        border-color: {border_f};
                    }}
                    QPushButton:pressed {{
                        background: {bg_inp};
                    }}
                """)

    # ------------------------------------------------------------------
    # Ensure title bar dark mode is set once the native handle exists
    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        try:
            _set_title_bar_dark(self.winId(), self._is_dark())
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI construction  (no inline color strings)
    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 15, 20, 15)

        self.advance_view_toggle = self._create_setting_row(
            "Advance View",
            "Enable advanced market view features"
        )
        self.advance_view_toggle.toggle.toggled.connect(self._on_setting_changed)

        self.one_click_trade_toggle = self._create_setting_row(
            "One Click Trade",
            "Execute trades with a single click"
        )
        self.one_click_trade_toggle.toggle.toggled.connect(self._on_setting_changed)

        layout.addWidget(self.advance_view_toggle)
        layout.addWidget(self.one_click_trade_toggle)
        layout.addWidget(self._create_default_lot_row())
        layout.addStretch()

    def _create_setting_row(self, title: str, description: str = "") -> QWidget:
        """Row with a title, optional description and a toggle.
        Labels carry objectNames so apply_theme() can target them."""
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 6, 0, 6)

        col = QVBoxLayout()
        col.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("SettingTitle")
        col.addWidget(title_lbl)

        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setObjectName("SettingDesc")
            col.addWidget(desc_lbl)

        toggle = ToggleSwitch()
        row_layout.addLayout(col)
        row_layout.addStretch()
        row_layout.addWidget(toggle)

        container.toggle = toggle
        return container

    def _create_default_lot_row(self) -> QWidget:
        """Lot row — buttons and input have no inline colours; apply_theme() handles them."""
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 6, 0, 6)

        label = QLabel("Default Lot")
        label.setObjectName("SettingLabel")

        self.down_arrow_btn = _IconButton("▼")
        self.down_arrow_btn.setFixedSize(28, 28)
        self.down_arrow_btn.clicked.connect(self._decrease_lot)
        self.down_arrow_btn.setEnabled(False)

        self.default_lot_input = QLineEdit("0.01")
        self.default_lot_input.setFixedWidth(60)
        self.default_lot_input.setAlignment(Qt.AlignCenter)
        self.default_lot_input.setValidator(QDoubleValidator(0.01, 100.0, 2))
        self.default_lot_input.setReadOnly(True)
        self.default_lot_input.textChanged.connect(self._on_lot_value_changed)

        self.up_arrow_btn = _IconButton("▲")
        self.up_arrow_btn.setFixedSize(28, 28)
        self.up_arrow_btn.clicked.connect(self._increase_lot)
        self.up_arrow_btn.setEnabled(False)

        self.edit_btn = _IconButton("✏")
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setCheckable(True)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)

        self.default_lot_toggle = ToggleSwitch()
        self.default_lot_toggle.toggled.connect(self._on_default_lot_toggled)

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(self.down_arrow_btn)
        row_layout.addWidget(self.default_lot_input)
        row_layout.addWidget(self.up_arrow_btn)
        row_layout.addWidget(self.edit_btn)
        row_layout.addSpacing(6)
        row_layout.addWidget(self.default_lot_toggle)

        return container

    # ------------------------------------------------------------------
    # Edit mode — apply_theme() replaces all inline style overrides
    # ------------------------------------------------------------------
    def _toggle_edit_mode(self):
        is_editing = self.edit_btn.isChecked()
        self.default_lot_input.setReadOnly(not is_editing)
        self.down_arrow_btn.setEnabled(is_editing)
        self.up_arrow_btn.setEnabled(is_editing)
        self.edit_btn.setText("✓" if is_editing else "✏")

        if not is_editing:
            self._on_setting_changed()

        # Refresh all colours to match the new edit / view state
        self.apply_theme()

        if is_editing:
            self.default_lot_input.setFocus()
            self.default_lot_input.selectAll()

    # ------------------------------------------------------------------
    # Value helpers
    # ------------------------------------------------------------------
    def _increase_lot(self):
        try:
            v = float(self.default_lot_input.text())
            self.default_lot_input.setText(f"{min(100.0, v + 0.01):.2f}")
        except Exception:
            pass

    def _decrease_lot(self):
        try:
            v = float(self.default_lot_input.text())
            self.default_lot_input.setText(f"{max(0.01, v - 0.01):.2f}")
        except Exception:
            pass

    def _on_default_lot_toggled(self, checked: bool):
        if not checked:
            self.default_lot_input.setText("0.01")
            self.edit_btn.setChecked(False)
            self._toggle_edit_mode()
        self._on_setting_changed()

    def _on_lot_value_changed(self):
        if not self.edit_btn.isChecked():
            self._on_setting_changed()

    # ------------------------------------------------------------------
    # Settings I/O
    # ------------------------------------------------------------------
    def get_settings(self) -> dict:
        try:
            lot = float(self.default_lot_input.text())
        except ValueError:
            lot = 0.01

        enabled = self.default_lot_toggle.isChecked()
        return {
            'advance_view':       self.advance_view_toggle.toggle.isChecked(),
            'one_click_trade':    self.one_click_trade_toggle.toggle.isChecked(),
            'default_lot':        lot if enabled else 0.01,
            'default_lot_enabled': enabled,
        }

    def set_settings(self, settings: dict):
        self.advance_view_toggle.toggle.setChecked(
            settings.get('advance_view', False))
        self.one_click_trade_toggle.toggle.setChecked(
            settings.get('one_click_trade', False))
        self.default_lot_input.setText(
            f"{settings.get('default_lot', 0.01):.2f}")
        self.default_lot_toggle.setChecked(
            settings.get('default_lot_enabled', False))

    def _on_setting_changed(self):
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)

    def accept(self):
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)
        super().accept()