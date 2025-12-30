from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtGui import QAction
from Main_page_ui import Ui_MainWindow
from statusbar.status_bar_manager import StatusBarManager
from Login.login_page import LoginPage
from Forgot_password.forgot_password_controller import ForgotPasswordDialog
import auth.session as session


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ---- Status bar ----
        self.status_manager = StatusBarManager(self.ui.statusBar)

        # Track sign-in state
        self._signed_in_user = None
        self._sign_out_action = None

        # ---- Menu / Toolbar actions ----
        self._connect_actions()

        # Restore session if we already have credentials persisted
        try:
            if session.is_signed_in():
                user = session.get_current_user()
                if user:
                    self._signed_in_user = user
                    self.setWindowTitle(f"JetFyx — {self._signed_in_user}")

                    # Add Sign Out action so user can sign out immediately
                    self._sign_out_action = QAction("Sign Out", self)
                    self._sign_out_action.triggered.connect(self._handle_sign_out)
                    try:
                        self.ui.menuFile.addAction(self._sign_out_action)
                    except Exception:
                        self.menuBar().addAction(self._sign_out_action)

                    try:
                        self.ui.actionOpen_an_Account.setEnabled(False)
                    except Exception:
                        pass
        except Exception:
            # Best-effort: if anything fails here, don't block startup
            logger = __import__("logging").getLogger(__name__)
            logger.exception("Failed to restore session on startup")

    def _connect_actions(self):
        self.ui.actionExit.triggered.connect(self.close)
        # Keep the open account action for login
        self.ui.actionOpen_an_Account.triggered.connect(self._open_login_dialog)

    # ---------------- LOGIN DIALOG ----------------

    def _open_login_dialog(self):
        self.login_dialog = LoginPage(self)
        self.login_dialog.login_success.connect(self._on_login_success)
        # Open the forgot password dialog when login page emits the signal
        self.login_dialog.forgot_password_requested.connect(self._open_forgot_dialog)
        # Open the create account dialog when requested from the login page
        try:
            from Create_Account import CreateAccountDialog
            self.login_dialog.create_account_requested.connect(self._open_create_account_dialog)
        except Exception:
            # keep behavior tolerant if module not present
            pass
        self.login_dialog.exec()

    def _open_create_account_dialog(self):
        try:
            from Create_Account import CreateAccountDialog
            d = CreateAccountDialog(self)
            d.exec()
        except Exception:
            logger = __import__('logging').getLogger(__name__)
            logger.exception("Failed to open Create Account dialog")

    def _open_forgot_dialog(self):
        try:
            d = ForgotPasswordDialog(self)
            d.exec()
        except Exception:
            # Best-effort: don't crash the whole app if dialog cannot be displayed
            logger = __import__('logging').getLogger(__name__)
            logger.exception("Failed to open Forgot Password dialog")


    def _on_login_success(self, email: str):
        # Close the dialog if still open
        print("Login successful → updating UI")
        try:
            self.login_dialog.close()
        except Exception:
            pass

        # Remember signed in user and update window title
        self._signed_in_user = email or session.get_current_user()
        if self._signed_in_user:
            self.setWindowTitle(f"JetFyx — {self._signed_in_user}")
        else:
            self.setWindowTitle("JetFyx")

        # Add Sign Out action if not present
        if self._sign_out_action is None:
            self._sign_out_action = QAction("Sign Out", self)
            self._sign_out_action.triggered.connect(self._handle_sign_out)
            # Add to File menu so it looks native
            try:
                self.ui.menuFile.addAction(self._sign_out_action)
            except Exception:
                # Fallback: add to menubar
                self.menuBar().addAction(self._sign_out_action)

        # Optionally disable the login action while signed in
        try:
            self.ui.actionOpen_an_Account.setEnabled(False)
        except Exception:
            pass

    def _handle_sign_out(self):
        # Clear session token and user, then update UI
        session.sign_out()
        self._signed_in_user = None
        self.setWindowTitle("JetFyx")

        # Remove sign out action if it exists
        if self._sign_out_action is not None:
            try:
                self.ui.menuFile.removeAction(self._sign_out_action)
            except Exception:
                try:
                    self.menuBar().removeAction(self._sign_out_action)
                except Exception:
                    pass
            self._sign_out_action = None

        # Re-enable login
        try:
            self.ui.actionOpen_an_Account.setEnabled(True)
        except Exception:
            pass

        QMessageBox.information(self, "Signed out", "You have been signed out.")


