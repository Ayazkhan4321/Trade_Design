import sys

from PySide6.QtWidgets import QApplication
from MarketWatch_jetfyx.ui.market_widget import MarketWidget
from accounts.login_page import LoginPage
from MarketWatch_jetfyx.services import SettingsService, OrderService, PriceService
from accounts.store import AppStore
from MarketWatch_jetfyx.services.market_data_service import MarketDataService






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
            # Open forgot password dialog when requested from the login page
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
            # Persist full API response so other components (BottomBar) can
            # extract account balances and currencies.
            try:
                store.set_api_response(data)
            except Exception:
                pass
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


if __name__ == '__main__':
    app = MarketWatchApp()
    sys.exit(app.run())
