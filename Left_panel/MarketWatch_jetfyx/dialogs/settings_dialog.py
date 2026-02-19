"""
Settings Dialog - Application settings configuration
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QLineEdit, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
from MarketWatch_jetfyx.widgets.toggle_switch import ToggleSwitch


class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    settingsChanged = Signal(dict)  # Emits settings when changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setFixedSize(350, 180)
        
        # Current settings values
        self.settings = {
            'advance_view': False,
            'one_click_trade': False,
            'default_lot': 0.01,
            'default_lot_enabled': False
        }
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Advance View setting
        self.advance_view_toggle = self._create_setting_row(
            "Advance View",
            "Enable advanced market view features"
        )
        self.advance_view_toggle.toggle.toggled.connect(self._on_setting_changed)
        
        # One Click Trade setting
        self.one_click_trade_toggle = self._create_setting_row(
            "One Click Trade",
            "Execute trades with a single click"
        )
        self.one_click_trade_toggle.toggle.toggled.connect(self._on_setting_changed)
        
        # Default Lot setting
        default_lot_widget = self._create_default_lot_row()
        
        # Add all to layout
        layout.addWidget(self.advance_view_toggle)
        layout.addWidget(self.one_click_trade_toggle)
        layout.addWidget(default_lot_widget)
        layout.addStretch()
    
    def _create_setting_row(self, title, description=""):
        """Create a setting row with label and toggle"""
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 6, 0, 6)
        
        # Label container
        label_container = QVBoxLayout()
        label_container.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
        label_container.addWidget(title_label)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 11px; color: #666;")
            label_container.addWidget(desc_label)
        
        # Toggle switch
        toggle = ToggleSwitch()
        
        row_layout.addLayout(label_container)
        row_layout.addStretch()
        row_layout.addWidget(toggle)
        
        # Store the toggle for later access
        container.toggle = toggle
        
        return container
    
    def _create_default_lot_row(self):
        """Create the default lot setting row with input and toggle"""
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 6, 0, 6)
        
        # Label
        label = QLabel("Default Lot")
        label.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
        
        # Down arrow button
        self.down_arrow_btn = QPushButton("▼")
        self.down_arrow_btn.setFixedSize(32, 32)
        self.down_arrow_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-right: none;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                color: #666;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e3f2fd;
                border-color: #1976d2;
            }
        """)
        self.down_arrow_btn.clicked.connect(self._decrease_lot)
        self.down_arrow_btn.setEnabled(False)  # Initially disabled
        
        # Input field
        self.default_lot_input = QLineEdit()
        self.default_lot_input.setText("0.01")
        self.default_lot_input.setFixedWidth(70)
        self.default_lot_input.setAlignment(Qt.AlignCenter)
        self.default_lot_input.setValidator(QDoubleValidator(0.01, 100.0, 2))
        self.default_lot_input.setReadOnly(True)  # Initially read-only
        self.default_lot_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-left: none;
                border-right: none;
                font-size: 13px;
                font-weight: 600;
                background: #f5f5f5;
                color: #999;
            }
            QLineEdit:!read-only {
                background: white;
                color: #333;
                border: 2px solid #1976d2;
                border-left: none;
                border-right: none;
            }
        """)
        self.default_lot_input.textChanged.connect(self._on_lot_value_changed)
        
        # Up arrow button
        self.up_arrow_btn = QPushButton("▲")
        self.up_arrow_btn.setFixedSize(32, 32)
        self.up_arrow_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-left: none;
                color: #666;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e3f2fd;
                border-color: #1976d2;
            }
        """)
        self.up_arrow_btn.clicked.connect(self._increase_lot)
        self.up_arrow_btn.setEnabled(False)  # Initially disabled
        
        # Edit button (pencil icon) - unlocks editing
        self.edit_btn = QPushButton("✏")
        self.edit_btn.setFixedSize(32, 32)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-left: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                color: #1976d2;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e3f2fd;
                border-color: #1976d2;
            }
            QPushButton:pressed {
                background: #bbdefb;
            }
        """)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        self.edit_btn.setCheckable(True)
        
        # Toggle switch
        self.default_lot_toggle = ToggleSwitch()
        self.default_lot_toggle.toggled.connect(self._on_default_lot_toggled)
        
        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(self.down_arrow_btn)
        row_layout.addWidget(self.default_lot_input)
        row_layout.addWidget(self.up_arrow_btn)
        row_layout.addWidget(self.edit_btn)
        row_layout.addSpacing(10)
        row_layout.addWidget(self.default_lot_toggle)
        
        return container
    
    def _toggle_edit_mode(self):
        """Toggle edit mode for default lot input"""
        is_editing = self.edit_btn.isChecked()
        
        # Enable/disable input and arrows
        self.default_lot_input.setReadOnly(not is_editing)
        self.down_arrow_btn.setEnabled(is_editing)
        self.up_arrow_btn.setEnabled(is_editing)
        
        if is_editing:
            # Edit mode - enable input
            self.default_lot_input.setFocus()
            self.default_lot_input.selectAll()
            self.edit_btn.setText("✓")  # Change to checkmark
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background: #4caf50;
                    border: 1px solid #4caf50;
                    border-left: none;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #45a049;
                }
            """)
        else:
            # View mode - disable input and save value
            self.edit_btn.setText("✏")
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    border-left: none;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                    color: #1976d2;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #e3f2fd;
                    border-color: #1976d2;
                }
            """)
            self._on_setting_changed()
    
    def _increase_lot(self):
        """Increase lot value"""
        try:
            current = float(self.default_lot_input.text())
            new_value = min(100.0, current + 0.01)
            self.default_lot_input.setText(f"{new_value:.2f}")
        except:
            pass
    
    def _decrease_lot(self):
        """Decrease lot value"""
        try:
            current = float(self.default_lot_input.text())
            new_value = max(0.01, current - 0.01)
            self.default_lot_input.setText(f"{new_value:.2f}")
        except:
            pass
    
    def _on_default_lot_toggled(self, checked):
        """Handle default lot toggle change"""
        if not checked:
            # When turned OFF, reset to 0.01 and disable editing
            self.default_lot_input.setText("0.01")
            self.edit_btn.setChecked(False)
            self._toggle_edit_mode()
        
        self._on_setting_changed()
    
    def _on_lot_value_changed(self):
        """Handle lot value text change"""
        # Only emit if not in edit mode (i.e., when user finishes editing)
        if not self.edit_btn.isChecked():
            self._on_setting_changed()
    
    def _apply_styles(self):
        """Apply dialog styles"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-radius: 8px;
            }
        """)
    
    def get_settings(self):
        """Get current settings values"""
        try:
            default_lot_value = float(self.default_lot_input.text())
        except ValueError:
            default_lot_value = 0.01
        
        # If default lot is disabled, always return 0.01
        is_enabled = self.default_lot_toggle.isChecked()
        if not is_enabled:
            default_lot_value = 0.01
        
        return {
            'advance_view': self.advance_view_toggle.toggle.isChecked(),
            'one_click_trade': self.one_click_trade_toggle.toggle.isChecked(),
            'default_lot': default_lot_value,
            'default_lot_enabled': is_enabled
        }
    
    def set_settings(self, settings):
        """Set settings values"""
        self.advance_view_toggle.toggle.setChecked(settings.get('advance_view', False))
        self.one_click_trade_toggle.toggle.setChecked(settings.get('one_click_trade', False))
        
        # Set default lot value and enabled state
        default_lot = settings.get('default_lot', 0.01)
        default_lot_enabled = settings.get('default_lot_enabled', False)
        
        self.default_lot_input.setText(f"{default_lot:.2f}")
        self.default_lot_toggle.setChecked(default_lot_enabled)
    
    def _on_setting_changed(self):
        """Handle any setting change - emit immediately"""
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)
    
    def accept(self):
        """Handle dialog acceptance"""
        self.settings = self.get_settings()
        self.settingsChanged.emit(self.settings)
        super().accept()
