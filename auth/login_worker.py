from PySide6.QtCore import QObject, Signal
from auth.auth_service import authenticate


class LoginWorker(QObject):
    finished = Signal(bool, str)

    def run(self, account_type, email, password):
        success, message = authenticate(account_type, email, password)
        self.finished.emit(success, message)
