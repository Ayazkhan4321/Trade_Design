from PySide6.QtWidgets import QLabel

class ProfileBlock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Default")
        self.setMinimumWidth(80)
