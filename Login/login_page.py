"""login_page.py – Login dialog with live theme support.

The dialog now connects to ThemeManager.theme_changed so every element
(background, input borders, buttons, labels) automatically updates whenever
the user switches between Dark / Light / Crazy / Time-Based themes.
"""
from PySide6.QtWidgets import QDialog, QButtonGroup, QMessageBox
from PySide6.QtCore import Signal, QThread
from .Login_page_ui import Ui_Dialog
from auth.login_worker import LoginWorker


class LoginPage(QDialog):
    login_success = Signal(str)
    create_account_requested = Signal()
    forgot_password_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self._last_email = None
        

        self._setup_toggle_buttons()
        self._setup_defaults()
        self._connect_signals()

        # ── Apply initial theme-aware styles ──
        try:
            from . import login_style as style
            style.apply_theme_to_login(self, self.ui)
        except Exception:
            pass

        # ── Subscribe to future theme changes ──
        try:
            from Theme.theme_manager import ThemeManager
            from . import login_style as _style
            ThemeManager.instance().theme_changed.connect(
                lambda name, tokens: _style.apply_theme_to_login(self, self.ui)
            )
        except Exception:
            pass

        self.setModal(True)
        self.setWindowTitle("Login")

    # ──────────────────────────── Setup ────────────────────────────────────────

    def _setup_defaults(self):
        self.ui.btn_live.setChecked(True)
        self.ui.input_password.setEchoMode(self.ui.input_password.EchoMode.Password)

    def _setup_toggle_buttons(self):
        self.account_group = QButtonGroup(self)
        self.account_group.setExclusive(True)
        self.account_group.addButton(self.ui.btn_live)
        self.account_group.addButton(self.ui.btn_demo)

    def _connect_signals(self):
        self.ui.btn_signin.clicked.connect(self._handle_login)
        self.ui.lbl_create_account.mousePressEvent = self._create_account_clicked
        self.ui.lbl_forgot_password.mousePressEvent = self._forgot_password_clicked

    # ──────────────────────────── Login ────────────────────────────────────────

    def _handle_login(self):
        email        = self.ui.input_email.text().strip()
        password     = self.ui.input_password.text()
        account_type = "live" if self.ui.btn_live.isChecked() else "demo"

        if not email or not password:
            self._show_error("Missing Information", "Email and password are required.")
            return

        self._last_email = email
        self.ui.btn_signin.setEnabled(False)

        self.thread = QThread(self)
        self.worker = LoginWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(lambda: self.worker.run(account_type, email, password))
        self.worker.finished.connect(self._on_login_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_login_result(self, success, message, response_data=None):
        self.ui.btn_signin.setEnabled(True)

        if not success:
            self._show_error("Login Failed", message)
            return

        try:
            self.response_data = response_data
        except Exception:
            self.response_data = None

        email = None
        try:
            if isinstance(response_data, dict):
                data = response_data.get("data", response_data)
                if isinstance(data, dict):
                    email = data.get("email")
        except Exception:
            email = None

        if not email:
            email = self._last_email or ""

        try:
            self.login_success.emit(email)
        except Exception:
            pass

        self.accept()

    # ──────────────────────────── Label Actions ─────────────────────────────────

    def _create_account_clicked(self, event):
        self.create_account_requested.emit()

    def _forgot_password_clicked(self, event):
        self.forgot_password_requested.emit()

    # ──────────────────────────── Helpers ──────────────────────────────────────

    def _show_error(self, title, message):
        QMessageBox.warning(self, title, message)