from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt


class OrdersEmptyState(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed   # 🔒 IMPORTANT
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("No open orders")
        label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
            }
        """)

        layout.addWidget(label)
