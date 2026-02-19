from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Signal

class LotPresetWidget(QWidget):
    lotChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons = {}

        for lot in (0.01, 0.10, 1.00):
            btn = QPushButton(f"{lot:.2f}")
            btn.setCheckable(True)
            btn.setFixedSize(24, 20)
            btn.setProperty("lot", lot)
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #333;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 8px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #e3f2fd;
                    border-color: #1976d2;
                }
                QPushButton:checked {
                    background: #1976d2;
                    color: white;
                    border-color: #1976d2;
                }
            """)
            layout.addWidget(btn)
            self.group.addButton(btn)
            self.buttons[lot] = btn

        # Set default selection
        self.buttons[0.01].setChecked(True)

    def get_selected_lot(self):
        """Get the currently selected lot value"""
        checked_btn = self.group.checkedButton()
        if checked_btn:
            return checked_btn.property("lot")
        return 0.01  # Default
