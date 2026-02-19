"""Wrapper that re-exports the central LoginWorker from `auth.login_worker`.

Left-panel code importing `Left_panel.accounts.login_worker.LoginWorker` will
continue to work during migration.
"""
from auth.login_worker import LoginWorker

__all__ = ["LoginWorker"]
from PySide6.QtCore import QObject, Signal
from accounts.auth_service import authenticate


class LoginWorker(QObject):
    finished = Signal(bool, str, object)  # success, message, response_data

    def run(self, account_type, email, password):
        success, message, response_data = authenticate(account_type, email, password)
        self.finished.emit(success, message, response_data)
