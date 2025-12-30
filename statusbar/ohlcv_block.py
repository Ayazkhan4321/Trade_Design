from PySide6.QtWidgets import QLabel

class OHLCVBlock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(350)
        self.clear_data()

    def clear_data(self):
        self.setText("O: -   H: -   L: -   C: -   V: -")

    def update_data(self, o, h, l, c, v):
        self.setText(
            f"O: {o:.5f}   H: {h:.5f}   L: {l:.5f}   "
            f"C: {c:.5f}   V: {v}"
        )
