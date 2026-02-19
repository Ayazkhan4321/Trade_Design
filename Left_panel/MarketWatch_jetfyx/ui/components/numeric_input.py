"""
Numeric Input Component - Input field with up/down buttons
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator


class NumericInput(QWidget):
    """Reusable numeric input component with increment/decrement buttons"""
    
    valueChanged = Signal(float)
    
    def __init__(self, label_text="", placeholder="", default_value=0.0, decimals=5, parent=None):
        super().__init__(parent)
        
        self.label_text = label_text
        self.placeholder = placeholder
        self.default_value = default_value
        self.decimals = decimals
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        if self.label_text:
            label = QLabel(self.label_text)
            label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
            layout.addWidget(label)
        
        # Control row
        control_row = QHBoxLayout()
        control_row.setSpacing(0)
        
        # Down button
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(40, 40)
        self.btn_down.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-right: none;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                font-size: 12px;
                color: #666;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.btn_down.clicked.connect(self.decrease_value)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder)
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setFixedHeight(40)
        
        # Set validator for numeric input
        if self.decimals > 0:
            self.input_field.setValidator(QDoubleValidator(0.0, 999999.99999, self.decimals))
        
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ddd;
                border-left: none;
                border-right: none;
                font-size: 13px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
                border-left: none;
                border-right: none;
            }
        """)
        self.input_field.textChanged.connect(self._on_text_changed)
        
        # Up button
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(40, 40)
        self.btn_up.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-left: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                font-size: 12px;
                color: #666;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.btn_up.clicked.connect(self.increase_value)
        
        control_row.addWidget(self.btn_down)
        control_row.addWidget(self.input_field)
        control_row.addWidget(self.btn_up)
        
        layout.addLayout(control_row)
    
    def get_value(self):
        """Get current value"""
        try:
            text = self.input_field.text()
            if text:
                return float(text)
            return self.default_value
        except:
            return self.default_value
    
    def set_value(self, value):
        """Set value"""
        self.input_field.setText(f"{value:.{self.decimals}f}")
    
    def increase_value(self):
        """Increase value"""
        current = self.get_value()
        step = 10 ** (-self.decimals)  # Step based on decimals (0.00001 for 5 decimals)
        new_value = current + step
        self.set_value(new_value)
    
    def decrease_value(self):
        """Decrease value"""
        current = self.get_value()
        step = 10 ** (-self.decimals)
        new_value = max(0, current - step)
        self.set_value(new_value)
    
    def _on_text_changed(self, text):
        """Handle text change"""
        if text:
            try:
                value = float(text)
                self.valueChanged.emit(value)
            except:
                pass
    
    def clear(self):
        """Clear the input"""
        self.input_field.clear()
    
    def get_text(self):
        """Get raw text"""
        return self.input_field.text()
