"""
Toggle Switch Widget - Reusable toggle switch component
"""
from PySide6.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    """Custom toggle switch widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 44px;
                height: 22px;
                border-radius: 11px;
                background: #e0e0e0;
                border: 1px solid #ccc;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50, stop:1 #66bb6a);
                border: 1px solid #4caf50;
            }
            QCheckBox::indicator:hover {
                background: #d0d0d0;
                border: 1px solid #999;
            }
            QCheckBox::indicator:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #45a049, stop:1 #5cb85c);
            }
        """)
