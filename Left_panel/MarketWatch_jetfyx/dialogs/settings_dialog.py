"""
Settings Dialog - Application settings configuration
Fully Theme-Aware with Dynamic Backgrounds and Precise Anchoring
"""
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent
from PySide6.QtGui import QDoubleValidator, QColor, QPalette, QFont, QPainter, QCursor
from MarketWatch_jetfyx.widgets.toggle_switch import ToggleSwitch

try:
    from Theme.theme_manager import ThemeManager as _ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _ThemeManager = None
    _THEME_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Dimmer Overlay
# ─────────────────────────────────────────────────────────────────────────────
class DimmerOverlay(QWidget):
    """A full-screen overlay that dims the main window dynamically."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Standard dark overlay for premium lightbox effect
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.45);") 
        
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
            parent.installEventFilter(self)
            
    def eventFilter(self, obj, event):
        if obj == self.parent_widget and event.type() == QEvent.Resize:
            self.setGeometry(0, 0, self.parent_widget.width(), self.parent_widget.height())
        return super().eventFilter(obj, event)

class _IconButton(QPushButton):
    """Theme-aware custom button for lot controls."""
    def __init__(self, text, color="#4a5568", parent=None):
        super().__init__(text, parent)
        self._icon_color = color

    def paintEvent(self, event):
        from PySide6.QtWidgets import QStyleOptionButton, QStyle
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_PushButtonBevel, opt, painter, self)
        painter.setPen(QColor(self._icon_color))
        font = QFont("Segoe UI Symbol", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())  
        painter.end()

# ─────────────────────────────────────────────────────────────────────────────
# Main Settings Dialog
# ─────────────────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    settingsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        # Ensure enough width for all bold text and controls
        self.setMinimumWidth(360) 

        self.dimmer = None
        self.settings = {
            'advance_view': False,
            'one_click_trade': False,
            'default_lot': 0.01,
            'default_lot_enabled': False
        }

        self._setup_ui()
        self.apply_theme()

        # Listen for global theme changes to update background and text colors instantly
        if _THEME_AVAILABLE:
            try:
                _ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

    def exec(self):
        self.setAttribute(Qt.WA_Moved, True)
        self.adjustSize()
        
        main_window = None
        for w in QApplication.topLevelWidgets():
            if w.inherits("QMainWindow"):
                main_window = w
                break
                
        if main_window:
            self.dimmer = DimmerOverlay(main_window)
            self.dimmer.show()
            self.dimmer.raise_()
            
        self._snap_to_position()
        result = super().exec()
        
        if self.dimmer:
            self.dimmer.hide()
            self.dimmer.deleteLater()
            self.dimmer = None
        return result

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._snap_to_position)

    def _snap_to_position(self):
        """Anchors the popup immediately to the right of the Settings gear icon."""
        try:
            parent = self.parent()
            btn = None
            if parent and hasattr(parent, 'tab_bar'):
                from PySide6.QtWidgets import QAbstractButton
                btns = parent.tab_bar.findChildren(QAbstractButton)
                if btns:
                    btn = btns[-1] 

            if btn and btn.isVisible():
                btn_pos = btn.mapToGlobal(QPoint(0, 0))
                # Snaps to side of icon with a clean offset
                x = btn_pos.x() + btn.width() + 4
                y = btn_pos.y() - 15 
                self.move(x, y)
        except Exception:
            pass

    def apply_theme(self):
        """Applies dynamic theme tokens to ensure the popup matches the rest of the app."""
        t = {}
        if _THEME_AVAILABLE:
            t = _ThemeManager.instance().tokens()

        # 🟢 THEME FIX: Dynamically fetch current background and text tokens
        bg       = t.get("bg_popup", t.get("bg_panel", "#ffffff"))
        text_p   = t.get("text_primary", "#1a202c")
        text_s   = t.get("text_secondary", "#4a5568")
        border   = t.get("border_primary", "#e5e7eb")

        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            
            QFrame#MainContainer {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            
            QLabel#HeaderTitle {{
                color: {text_p};
                font-size: 16px;
                font-weight: 800; /* Extra bold for visibility */
                background: transparent;
            }}
            
            QPushButton#HeaderCloseBtn {{
                background-color: transparent;
                color: {text_s}; 
                font-size: 18px; 
                font-weight: bold;
                border: none;
                padding: 5px;
            }}
            
            QPushButton#HeaderCloseBtn:hover {{
                color: #ef4444; /* Standard hover feedback */
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            }}
            
            /* BOLD row text that adapts to theme color */
            QLabel#SettingTitle, QLabel#SettingLabel {{
                color: {text_p};
                font-weight: 800; 
                font-size: 14px;
                background: transparent;
            }}
            
            QLabel {{ color: {text_p}; background: transparent; }}
            QWidget {{ background: transparent; }}
        """)

    def _setup_ui(self):
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_container)
        
        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(20, 16, 20, 20)
        self.layout.setSpacing(18)

        # Header with high-contrast Close Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        title_lbl = QLabel("Settings")
        title_lbl.setObjectName("HeaderTitle")
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("HeaderCloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        self.layout.addLayout(header_layout)

        self.advance_view_toggle = self._create_setting_row("Advance View", "Enable advanced market view features")
        self.one_click_trade_toggle = self._create_setting_row("One Click Trade", "Execute trades with a single click")

        self.layout.addWidget(self.advance_view_toggle)
        self.layout.addWidget(self.one_click_trade_toggle)
        self.layout.addWidget(self._create_default_lot_row())
        self.layout.addStretch()

    def _create_setting_row(self, title: str, description: str = "") -> QWidget:
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        col = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("SettingTitle") 
        col.addWidget(title_lbl)
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setObjectName("SettingDesc")
            desc_lbl.setStyleSheet("font-size: 11px; opacity: 0.8;")
            col.addWidget(desc_lbl)
        toggle = ToggleSwitch()
        row_layout.addLayout(col)
        row_layout.addStretch()
        row_layout.addWidget(toggle)
        container.toggle = toggle
        return container

    def _create_default_lot_row(self) -> QWidget:
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        label = QLabel("Default Lot")
        label.setObjectName("SettingLabel") 
        self.down_arrow_btn = _IconButton("▼")
        self.down_arrow_btn.setFixedSize(24, 28)
        self.default_lot_input = QLineEdit("0.01")
        self.default_lot_input.setFixedWidth(50)
        self.default_lot_input.setAlignment(Qt.AlignCenter)
        self.up_arrow_btn = _IconButton("▲")
        self.up_arrow_btn.setFixedSize(24, 28)
        self.edit_btn = _IconButton("✏")
        self.edit_btn.setFixedSize(28, 28)
        self.default_lot_toggle = ToggleSwitch()
        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(self.down_arrow_btn)
        row_layout.addWidget(self.default_lot_input)
        row_layout.addWidget(self.up_arrow_btn)
        row_layout.addWidget(self.edit_btn)
        row_layout.addWidget(self.default_lot_toggle)
        return container

    def _on_lot_value_changed(self):
        if not hasattr(self, 'edit_btn') or not self.edit_btn.isChecked():
            self._on_setting_changed()

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
        self.advance_view_toggle.toggle.setChecked(settings.get('advance_view', False))
        self.one_click_trade_toggle.toggle.setChecked(settings.get('one_click_trade', False))
        self.default_lot_input.setText(f"{settings.get('default_lot', 0.01):.2f}")
        self.default_lot_toggle.setChecked(settings.get('default_lot_enabled', False))

    def _on_setting_changed(self):
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)

    def accept(self):
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)
        super().accept()