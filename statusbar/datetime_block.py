from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, QDateTime


class DateTimeBlock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(170)

        self._chart_override = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_system_time)
        self.timer.start(1000)

        self._update_system_time()

    def _update_system_time(self):
        try:
            if not self._chart_override:
                now = QDateTime.currentDateTime()
                self.setText(now.toString("yyyy.MM.dd hh:mm"))
        except Exception:
            # Ignore errors during shutdown or when widget is being destroyed
            pass

    # ===== Chart control =====
    def set_chart_time(self, qdatetime: QDateTime):
        self._chart_override = True
        self.setText(qdatetime.toString("yyyy.MM.dd hh:mm"))

    def clear_chart_time(self):
        self._chart_override = False
