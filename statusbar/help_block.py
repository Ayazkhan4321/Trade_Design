from PySide6.QtWidgets import QLabel

class HelpBlock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("For Help, press F1")
        self.setMinimumWidth(180)
