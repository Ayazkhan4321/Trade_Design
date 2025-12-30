from PySide6.QtWidgets import QDialog, QButtonGroup, QMessageBox
from PySide6.QtCore import Signal, QThread
from .Login_page_ui import Ui_Dialog
from auth.login_worker import LoginWorker


class LoginPage(QDialog):
    # Emit the email string on success so the main window can display who is
    # currently signed in.
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

        # Apply login page styles (hover for forgot password label)
        try:
            from . import login_style as style
            style.apply_login_styles(self.ui)
        except Exception:
            pass

        # Optional: Make dialog modal like MT5
        self.setModal(True)
        self.setWindowTitle("Login")



    # ---------------- SETUP ----------------

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

    # ---------------- LOGIN ----------------

    def _handle_login(self):
        email = self.ui.input_email.text().strip()
        password = self.ui.input_password.text()
        account_type = "live" if self.ui.btn_live.isChecked() else "demo"

        if not email or not password:
            self._show_error("Missing Information", "Email and password are required.")
            return

        # Remember email so we can emit it on success
        self._last_email = email

        self.ui.btn_signin.setEnabled(False)

        # Setup worker thread
        self.thread = QThread(self)
        self.worker = LoginWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(lambda: self.worker.run(account_type, email, password))

        self.worker.finished.connect(self._on_login_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_login_result(self, success, message):
        self.ui.btn_signin.setEnabled(True)

        if not success:
            # Show error only if login fails
            self._show_error("Login Failed", message)
            return

        # ✅ Login successful: emit signal (with email) and close dialog
        if self._last_email:
            self.login_success.emit(self._last_email)
        else:
            self.login_success.emit("")
        self.accept()  # Closes the dialog

    # ---------------- LABEL ACTIONS ----------------

    def _create_account_clicked(self, event):
        self.create_account_requested.emit()

    def _forgot_password_clicked(self, event):
        self.forgot_password_requested.emit()

    # ---------------- HELPERS ----------------

    def _show_error(self, title, message):
        QMessageBox.warning(self, title, message)
