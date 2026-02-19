from PySide6.QtCore import QObject, Signal
from auth.auth_service import authenticate_full


class LoginWorker(QObject):
    # Emit success, message, response_data
    finished = Signal(bool, str, object)

    def run(self, account_type, email, password):
        success, message, response_data = authenticate_full(account_type, email, password)
        self.finished.emit(success, message, response_data)
