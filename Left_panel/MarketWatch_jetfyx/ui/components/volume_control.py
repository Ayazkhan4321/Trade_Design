"""
Volume Control Component - Reusable volume input widget
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal
from MarketWatch_jetfyx.config.ui_config import BUTTON_STYLES, SIZES


class VolumeControl(QWidget):
    """Reusable volume control component"""
    
    volumeChanged = Signal(float)
    
    def __init__(self, default_volume=0.01, parent=None):
        super().__init__(parent)
        
        self.default_volume = default_volume
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        label = QLabel("Volume")
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        
        # Control row
        control_row = QHBoxLayout()
        control_row.setSpacing(5)
        
        # Decrease button
        self.btn_decrease = QPushButton("▼")
        self.btn_decrease.setFixedSize(*SIZES['button_medium'])
        self.btn_decrease.setStyleSheet(BUTTON_STYLES['standard'])
        self.btn_decrease.clicked.connect(self.decrease_volume)
        
        # Volume input
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setDecimals(2)
        self.volume_input.setMinimum(0.01)
        self.volume_input.setMaximum(100.0)
        self.volume_input.setSingleStep(0.01)
        self.volume_input.setValue(self.default_volume)
        self.volume_input.setAlignment(Qt.AlignCenter)
        self.volume_input.setFixedHeight(SIZES['input_height'])
        self.volume_input.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #1976d2;
                border-radius: 4px;
                font-size: 14px;
                padding: 5px;
            }
        """)
        self.volume_input.valueChanged.connect(self.volumeChanged.emit)
        
        # Increase button
        self.btn_increase = QPushButton("▲")
        self.btn_increase.setFixedSize(*SIZES['button_medium'])
        self.btn_increase.setStyleSheet(BUTTON_STYLES['standard'])
        self.btn_increase.clicked.connect(self.increase_volume)
        
        control_row.addWidget(self.btn_decrease)
        control_row.addWidget(self.volume_input)
        control_row.addWidget(self.btn_increase)
        
        layout.addWidget(label)
        layout.addLayout(control_row)
    
    def get_volume(self):
        """Get current volume"""
        return self.volume_input.value()
    
    def set_volume(self, volume):
        """Set volume"""
        self.volume_input.setValue(volume)
    
    def increase_volume(self):
        """Increase volume"""
        current = self.volume_input.value()
        self.volume_input.setValue(min(100.0, current + 0.01))
    
    def decrease_volume(self):
        """Decrease volume"""
        current = self.volume_input.value()
        self.volume_input.setValue(max(0.01, current - 0.01))
