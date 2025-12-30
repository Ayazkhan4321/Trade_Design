from PySide6.QtWidgets import QLabel

class SignalBlock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(120)
        self.update_signal("Idle")

    def update_signal(self, text):
        self.setText(text)
