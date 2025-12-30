"""UI controller for the Forgot Password dialog.

This file contains all UI behaviour for the forgot-password dialog: enabling/disabling
controls, input validation, launching a background worker to call the API and showing
friendly messages to the user. Keeping controller logic in one place keeps the UI
clean and testable.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QObject, Signal, QThread, Qt
from .forgot_password_ui import Ui_Forgot_Password
from .forgot_password_service import send_reset_link, _is_valid_email

logger = logging.getLogger(__name__)


class ForgotPasswordWorker(QObject):
    """Worker to run the network call off the UI thread.

    Supports cooperative cancellation via `cancel()` which sets a flag the
    worker checks before and after the network call. We cannot reliably
    abort an in-flight `requests` call, but cancelling prevents the result
    from being acted on and ensures a clean shutdown.
    """

    # Now emit whether the result is retryable to allow the UI to offer Retry
    finished = Signal(bool, str, bool)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = False

    def run(self, email: str) -> None:
        if self._cancelled:
            # Early exit if cancelled before starting
            self.finished.emit(False, "Cancelled", False)
            return

        res = send_reset_link(email)
        # backward-compat: support (bool, str) and (bool,str,bool)
        if isinstance(res, tuple) and len(res) == 3:
            success, message, retryable = res
        else:
            success, message = res
            retryable = False

        if self._cancelled:
            # If cancelled while the request was running, emit a cancelled marker
            self.finished.emit(False, "Cancelled", False)
            return

        self.finished.emit(success, message, retryable)

    def cancel(self) -> None:
        """Mark the worker as cancelled. This is cooperative; long-running
        work in `send_reset_link` should periodically check for cancellation
        if it supports interruption.
        """
        self._cancelled = True


class ForgotPasswordDialog(QDialog):
    """Dialog that wraps the generated UI and adds behaviour.

    Behavior:
    - The "Send Link" button is disabled until a valid email is entered.
    - Calls the API on a background thread and shows a message on completion.
    - Provides simple styling for disabled/enabled states.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.ui = Ui_Forgot_Password()
        self.ui.setupUi(self)

        # initial state
        self.ui.pb_send_link.setEnabled(False)
        # apply centralized styling module (keeps generated UI file unchanged)
        try:
            from . import forgot_password_style as style
            style.apply_forgot_password_styles(self.ui, self)
        except Exception:
            # If styling module fails, fall back to default in-place styles
            self._set_default_style()

        # connect signals
        self.ui.le_forgot_password.textChanged.connect(self._on_text_changed)
        self.ui.pb_send_link.clicked.connect(self._on_send_clicked)
        self.ui.pb_cancel.clicked.connect(self.reject)

        # thread placeholders
        self._thread: Optional[QThread] = None
        self._worker: Optional[ForgotPasswordWorker] = None

    def _set_default_style(self) -> None:
        """Apply minor styling improvements."""
        # Fallback / minimal default styles are kept here only in case the
        # external styling module fails to load at runtime.
        self.ui.pb_send_link.setStyleSheet(
            "QPushButton:disabled{ background-color:#bdbdbd; color:#6d6d6d;}"
        )
        self.ui.pb_send_link.setCursor(Qt.ForbiddenCursor)

        self.ui.le_forgot_password.setStyleSheet(
            "QLineEdit{ padding:6px; border:1px solid #cfcfcf; border-radius:3px;}"
            "QLineEdit:focus{ border:1px solid #1976D2; }"
        )

    def _on_text_changed(self, text: str) -> None:
        """Enable the send button only when a valid email is entered."""
        text = text.strip()
        if not text:
            self.ui.pb_send_link.setEnabled(False)
            self.ui.pb_send_link.setCursor(Qt.ForbiddenCursor)
            # normal border
            self.ui.le_forgot_password.setStyleSheet("QLineEdit{ padding:6px; border:1px solid #cfcfcf; border-radius:3px; }")
            return

        if _is_valid_email(text):
            self.ui.pb_send_link.setEnabled(True)
            self.ui.pb_send_link.setCursor(Qt.PointingHandCursor)
            # valid input - normal border
            self.ui.le_forgot_password.setStyleSheet("QLineEdit{ padding:6px; border:1px solid #cfcfcf; border-radius:3px; }")
        else:
            self.ui.pb_send_link.setEnabled(False)
            self.ui.pb_send_link.setCursor(Qt.ForbiddenCursor)
            # invalid input - red border
            self.ui.le_forgot_password.setStyleSheet("QLineEdit{ padding:6px; border:1px solid #d32f2f; border-radius:3px; }")

    def _on_send_clicked(self) -> None:
        email = self.ui.le_forgot_password.text().strip()
        # final client-side validation
        if not _is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return

        # disable inputs while request runs
        self.ui.le_forgot_password.setEnabled(False)
        self.ui.pb_send_link.setEnabled(False)
        self.ui.pb_send_link.setText("Sending...")

        # start worker thread
        self._thread = QThread()
        self._thread.setObjectName("ForgotPasswordThread")
        self._worker = ForgotPasswordWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(lambda: self._worker.run(email))
        # _on_finished now accepts (success, message, retryable)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        # clear cancellation marker when thread starts
        self._request_cancelled = False
        self._thread.start()

    def _on_finished(self, success: bool, message: str, retryable: bool = False) -> None:
        # Restore UI
        self.ui.le_forgot_password.setEnabled(True)
        self.ui.pb_send_link.setEnabled(True)
        self.ui.pb_send_link.setText("Send Link")

        # If the request was cancelled (user closed dialog), ignore showing messages
        if getattr(self, "_request_cancelled", False) or message == "Cancelled":
            self._worker = None
            return

        if success:
            QMessageBox.information(self, "Link sent", message)
            # Close the dialog on success to make UX smoother
            self.accept()
        else:
            # For retryable failures, offer the user an immediate retry option
            if retryable:
                choice = QMessageBox.question(
                    self,
                    "Failed to send link",
                    f"{message}\n\nWould you like to retry?",
                    QMessageBox.Retry | QMessageBox.Cancel,
                )
                if choice == QMessageBox.Retry:
                    # Re-initiate the send action; keep UI consistent
                    self._on_send_clicked()
            else:
                QMessageBox.warning(self, "Failed", message)

        # cleanup worker reference; thread will be cleared in _on_thread_finished
        self._worker = None

    def _on_thread_finished(self) -> None:
        """Clear the thread reference once it has fully finished."""
        self._thread = None

    def closeEvent(self, event) -> None:
        """Ensure any running worker thread is stopped before closing the dialog.

        If a worker is active we mark it cancelled and wait briefly for the
        thread to exit so we avoid the "QThread: Destroyed while thread is still
        running" warning.
        """
        if self._thread is not None and getattr(self._thread, "isRunning", lambda: False)():
            # mark as cancelled so finished handler ignores result
            self._request_cancelled = True
            if self._worker is not None:
                try:
                    self._worker.cancel()
                except Exception:
                    logger.exception("Failed to cancel worker")

            try:
                self._thread.quit()
                self._thread.wait(2000)
            except Exception:
                logger.exception("Failed while waiting for worker thread to stop")

            if self._thread is not None and getattr(self._thread, "isRunning", lambda: False)():
                logger.warning("ForgotPassword thread did not stop before dialog closed")

        # proceed with close
        super().closeEvent(event)