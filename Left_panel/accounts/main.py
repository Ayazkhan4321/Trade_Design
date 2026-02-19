import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from accounts.accounts_widget import AccountsWidget
from MarketWatch_jetfyx.services.settings_service import SettingsService
from MarketWatch_jetfyx.services.order_service import OrderService
from MarketWatch_jetfyx.services.price_service import PriceService
from MarketWatch_jetfyx.ui.market_widget import MarketWidget
from Login.login_page import LoginPage
from accounts.store import AppStore


class MainWindow(QMainWindow):
    def __init__(self, auto_login=True):
        super().__init__()
        self.setWindowTitle("Accounts Manager")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Market View tab (placeholder)
        market_widget = QWidget()
        market_widget.setStyleSheet("background-color: #ffffff;")
        self.tabs.addTab(market_widget, "Market View")

        # Accounts tab uses the new AccountsWidget
        self.accounts_widget = AccountsWidget(self)
        self.tabs.addTab(self.accounts_widget, "Accounts")

        # Optionally show login on start
        if auto_login:
            self.accounts_widget.show_login()
    
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Accounts Manager")
    app.setOrganizationName("YourOrganization")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# Alias for external references expecting AccountsWindow
AccountsWindow = MainWindow



# --- Merged from MarketWatch_jetfyx\main.py ---
class MarketWatchApp:
    """Main application class"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Initialize services
        self.settings_service = SettingsService()
        self.order_service = OrderService()
        self.price_service = PriceService()

        # Apply global styles
        self._apply_global_styles()

        # Show login dialog first and wire up login success
        self.login_dialog = LoginPage()
        self.login_dialog.login_success.connect(self.on_login_success)
        try:
            from Forgot_password.forgot_password_controller import ForgotPasswordDialog
            self.login_dialog.forgot_password_requested.connect(lambda: ForgotPasswordDialog().exec())
        except Exception:
            pass
    
        result = self.login_dialog.exec()
        if result != 1:
            sys.exit(0)  # User cancelled login

    def on_login_success(self, login_response):
        # Extract accountId from login_response
        data = login_response.get("data", login_response)
        accounts = data.get("accounts", [])
        account_id = None
        if accounts and isinstance(accounts, list) and len(accounts) > 0:
            account_id = accounts[0].get("accountId")
        # Fallback: try sharedAccounts if needed
        if not account_id:
            shared_accounts = data.get("sharedAccounts", [])
            if shared_accounts and len(shared_accounts) > 0:
                shared = shared_accounts[0].get("accounts", [])
                if shared and len(shared) > 0:
                    account_id = shared[0].get("accountId")

        # Create main widget without account_id; MarketWidget will subscribe
        # to AppStore.account_changed and start market services when account
        # is set via the store.
        self.main_widget = MarketWidget(
            settings_service=self.settings_service,
            order_service=self.order_service,
            price_service=self.price_service,
        )

        # Set the selected account in the central store so MarketWidget reacts
        try:
            store = AppStore.instance()
            # Determine account number and demo flag
            acct_number = None
            is_demo = False
            if accounts and isinstance(accounts, list) and len(accounts) > 0:
                first = accounts[0]
                acct_number = first.get("accountNumber") or first.get("number")
                is_demo = bool(first.get("isDemo", False))
            else:
                # try shared accounts fallback
                shared_accounts = data.get("sharedAccounts", [])
                if shared_accounts and len(shared_accounts) > 0:
                    shared = shared_accounts[0].get("accounts", [])
                    if shared and len(shared) > 0:
                        first = shared[0]
                        acct_number = first.get("accountNumber") or first.get("number")
                        is_demo = bool(first.get("isDemo", False))

            store.set_current_account(
                account_number=str(acct_number) if acct_number is not None else "",
                owner_email=data.get("email"),
                is_own=True,
                account_id=account_id,
                is_demo=is_demo,
            )
        except Exception:
            pass
        # Show the main widget
        self.main_widget.show()

        # Load window settings
        config = self.settings_service.get_settings()
        width = config.get('window_width', 420)
        height = config.get('window_height', 600)
        self.main_widget.resize(width, height)
    
    def _apply_global_styles(self):
        """Apply global application styles"""
        self.app.setStyleSheet("""
            QTableView::item:hover {
                background: transparent;
            }
            QTableView::item:selected {
                background: #bbdefb;
            }
            QTableView::item:selected:!active {
                background: #bbdefb;
            }
            QTreeWidget::item {
                background: transparent;
            }
            QTreeWidget::item:hover {
                background: transparent;
            }
            QTreeWidget::item:selected {
                background: transparent;
            }
            QTreeWidget::item:selected:hover {
                background: transparent;
            }
        """)
    
    def run(self):
        """Run the application"""
        self.main_widget.show()
        return self.app.exec()
# --- End merged block ---
