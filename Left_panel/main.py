"""
Main Application - Integrated Left Panel with MarketWatch and Accounts
Handles tab switching between Market View and Accounts modules
"""
import sys
import os
import importlib.util
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QDockWidget
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItemIterator

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MARKETWATCH_DIR = os.path.join(BASE_DIR, 'MarketWatch_jetfyx')
ACCOUNTS_DIR = os.path.join(BASE_DIR, 'accounts')
# Ensure project root is on sys.path so packages import normally
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# Import MarketWatch components (packages resolve from project root)
from MarketWatch_jetfyx.ui.market_widget import MarketWidget
from MarketWatch_jetfyx.services.settings_service import SettingsService
from MarketWatch_jetfyx.services.order_service import OrderService
from MarketWatch_jetfyx.services.price_service import PriceService

from accounts.accounts_widget import AccountsWidget


class LeftPanelApp(QMainWindow):
    """Main application window with integrated tabs"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trade Platform - Left Panel")
        self.setGeometry(100, 100, 420, 600)
        
        # Initialize services for MarketWatch
        self.settings_service = SettingsService()
        self.order_service = OrderService()
        self.price_service = PriceService()
        
        # Apply global styles
        self._apply_global_styles()
        
        # Setup UI
        self._setup_ui()
        
        # Show login dialog on startup
        self.show_login()
    
    def _apply_global_styles(self):
        """Apply global application styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: none;
                background-color: #ffffff;
                border-top: 2px solid #e0e0e0;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #666666;
                padding: 12px 24px;
                border: none;
                border-bottom: 3px solid transparent;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                background-color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                color: #1e293b;
                background-color: #fafafa;
            }
            QTableView::item:hover {
                background: transparent;
            }
            QTableView::item:selected {
                background: #bbdefb;
            }
            QTableView::item:selected:!active {
                background: #bbdefb;
            }
        """)
    
    def _setup_ui(self):
        """Setup the main window UI"""
        # Create a minimal central placeholder (main app content can go here)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Instantiate the two feature widgets
        self.market_widget = MarketWidget(
            settings_service=self.settings_service,
            order_service=self.order_service,
            price_service=self.price_service,
        )

        self.accounts_widget = AccountsWidget(self)

        # Create a dockable left panel that contains the market/accounts tabs
        from left_panel_widget import LeftPanelWidget
        left_panel = LeftPanelWidget(self.market_widget, self.accounts_widget, parent=self)

        dock = QDockWidget("Left Panel", self)
        dock.setWidget(left_panel)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # Route status messages from accounts widget to the main status bar
        try:
            self.accounts_widget.statusMessage.connect(self.statusBar().showMessage)
        except Exception:
            pass
    
    def show_login(self):
        """Show the login dialog on startup"""
        # Show the accounts login dialog hosted by the embedded AccountsWidget
        try:
            self.accounts_widget.show_login()
        except Exception:
            pass

        # Prefer API response from the accounts widget if available
        account_id = None
        try:
            api_resp = getattr(self.accounts_widget, 'api_response', None)
            if api_resp and isinstance(api_resp, dict):
                accounts_raw = api_resp.get('accounts') or api_resp.get('accounts', [])
                if accounts_raw and isinstance(accounts_raw, list) and len(accounts_raw) > 0:
                    first = accounts_raw[0]
                    account_id = first.get('accountNumber') or first.get('accountId') or first.get('number')
        except Exception:
            account_id = None
        # Try to set active account from either the returned id or the store's
        # current_account (some flows set current_account during login).
        from accounts.store import AppStore as _AppStore
        store = _AppStore.instance()

        # Prefer the explicit account_id returned from the dialog/widget
        final_account = account_id

        # Fallback to store.current_account if needed
        if not final_account:
            try:
                cur = store.get_current_account()
                if cur:
                    final_account = cur.get("account_id") or cur.get("account_number")
            except Exception:
                final_account = None

        if not final_account:
            print("No account selected or login cancelled — starting without active account.")
            return

        # Pass the selected account id to MarketWidget so it can start live updates
        try:
            self.market_widget.set_account_id(final_account)
        except Exception:
            pass
    
    def on_tab_changed(self, index):
        """Handle tab change events"""
        if index == 0:
            print("Switched to Market View")
        elif index == 1:
            print("Switched to Accounts")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window settings
        self.settings_service.set('window_width', self.width())
        self.settings_service.set('window_height', self.height())
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Trade Platform")
    app.setOrganizationName("TradePro")
    
    # Create and show main window
    window = LeftPanelApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
