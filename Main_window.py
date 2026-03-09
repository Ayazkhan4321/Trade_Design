from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from Main_page_ui import Ui_MainWindow
from statusbar.status_bar_manager import StatusBarManager
from Login.login_page import LoginPage
from Forgot_password.forgot_password_controller import ForgotPasswordDialog
import auth.session as session
import logging
from plugins.tradingview_plugin import TradingChartPlugin
# --- Theme system ---
try:
    from Theme.theme_manager import ThemeManager
    from Theme.theme_applier import ThemeApplier
    from Theme.theme_popup import ThemePopup
    _THEME_AVAILABLE = True
except Exception:
    _THEME_AVAILABLE = False

# Lazy imports for left panel integration (kept optional so app still runs without Left_panel)
try:
    import os, sys
    # Ensure Left_panel subpackages (MarketWatch_jetfyx, accounts) are importable
    _lp = os.path.join(os.path.dirname(__file__), "Left_panel")
    if _lp not in sys.path:
        sys.path.insert(0, _lp)
    from Left_panel.left_panel_widget import LeftPanelWidget
    from Left_panel.MarketWatch_jetfyx.ui.market_widget import MarketWidget
    from Left_panel.accounts.accounts_widget import AccountsWidget
    from Left_panel.MarketWatch_jetfyx.services.settings_service import SettingsService
    from Left_panel.MarketWatch_jetfyx.services.order_service import OrderService
    from Left_panel.MarketWatch_jetfyx.services.price_service import PriceService
    from PySide6.QtWidgets import QDockWidget
except Exception as e:
    import traceback
    print("Left_panel import failed:")
    traceback.print_exc()
    LeftPanelWidget = None
    MarketWidget = None
    AccountsWidget = None
    QDockWidget = None

print(f"Left panel available: {LeftPanelWidget is not None}, AccountsWidget: {AccountsWidget is not None}, MarketWidget: {MarketWidget is not None}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Prefer user-friendly dock behaviour and allow nested/tabbed docks
        try:
            self.setDockOptions(
                QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AnimatedDocks
            )
        except Exception:
            # If QMainWindow lacks these attributes on older bindings, ignore
            pass
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ---- Status bar ----
        self.status_manager = StatusBarManager(self.ui.statusBar)

        # ---- Theme system ----
        self._theme_popup = None
        if _THEME_AVAILABLE:
            try:
                mgr = ThemeManager.instance()
                ApplierCls = ThemeApplier
                ApplierCls.apply_to_app(mgr.tokens())
                mgr.theme_changed.connect(lambda name, t: ApplierCls.apply_to_app(t))
                self._theme_popup = ThemePopup(parent=self)
            except Exception as e:
                logging.getLogger(__name__).debug("Theme init failed: %s", e)

        # Track sign-in state
        self._signed_in_user = None
        self._sign_out_action = None

        #Theme toggle connection 
    

        # ---- Market Watch Dock Widget ----
        # Removed Market Watch dock widget
        self.market_watch_widget = None

        # ---- Menu / Toolbar actions ----
        self._connect_actions()
        


        # ---- Left Panel Dock (optional) ----
        try:
            if LeftPanelWidget and AccountsWidget and MarketWidget:
                # Construct widget instances and dock into main window
                self.accounts_widget = AccountsWidget(parent=self)
                # Provide MarketWidget with services so settings/price updates work
                settings_service = SettingsService()
                self.order_service = OrderService()
                price_service = PriceService()
                self.market_widget = MarketWidget(
                    settings_service=settings_service,
                    order_service=self.order_service,
                    price_service=price_service,
                )
                self.left_panel_widget = LeftPanelWidget(self.market_widget, self.accounts_widget, parent=self)

                self.left_panel_dock = QDockWidget("Left Panel", self)
                self.left_panel_dock.setObjectName("LeftPanelDock")
                self.left_panel_dock.setWidget(self.left_panel_widget)
                self.left_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.left_panel_dock)
                try:
                    # Configure dock features and visibility based on signed-in state
                    self.left_panel_dock.setFeatures(
                        QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
                    )
                    self.left_panel_dock.setFloating(False)
                    # Only show by default when a session exists
                    try:
                        from auth import session as _session
                        visible_by_default = _session.is_signed_in()
                    except Exception:
                        visible_by_default = False

                    # Ensure reasonable minimum width
                    try:
                        self.left_panel_widget.setMinimumWidth(200)
                    except Exception:
                        pass
                    self.left_panel_dock.setMinimumWidth(200)
                    self.left_panel_dock.setVisible(visible_by_default)

                    # Hook up the View menu action to toggle the dock (if present in UI)
                    try:
                        self.ui.actionMarket_Watch.setCheckable(True)
                        self.ui.actionMarket_Watch.setChecked(self.left_panel_dock.isVisible())
                        # When action is toggled, show/hide the dock
                        self.ui.actionMarket_Watch.toggled.connect(self.left_panel_dock.setVisible)
                        print("Market Watch action connected to left panel dock")
                    except Exception:
                        pass

                    self.left_panel_dock.show() if visible_by_default else None
                    print("Left panel dock created")
                except Exception:
                    pass

                # Forward status messages from the accounts widget to the main status bar
                # Forward status messages from the accounts widget to the main status bar
                try:
                    self.accounts_widget.statusMessage.connect(lambda msg, timeout=0: self.statusBar().showMessage(msg, timeout))
                except Exception:
                    pass

                # Forward login success from accounts widget to main window UI
                try:
                    if hasattr(self.accounts_widget, 'login_success'):
                        self.accounts_widget.login_success.connect(self._on_login_success)
                except Exception:
                    pass

                # Keep menu action in sync if present
                try:
                    self.left_panel_dock.visibilityChanged.connect(self._on_market_watch_visibility_changed)
                except Exception:
                    pass
        
        except Exception:
            # Best-effort integration: don't prevent app startup if left panel cannot be created
            pass

        # ---- Orders Dock (optional) ----
        # Defer Orders dock creation until the user logs in (mirror left panel behaviour)
        self.orders_dock = None
        self.orders_widget = None

        # Create the orders dock once (hidden). This reserves layout space and
        # prevents the central widget from collapsing the dock to zero height.
        try:
            self._create_orders_dock()
            try:
                if self.orders_dock is not None:
                    self.orders_dock.hide()
            except Exception:
                pass
        except Exception:
            logging.exception("Failed initial orders dock creation")

        # Restore session if we already have credentials persisted
        if session.is_signed_in():
            user = session.get_current_user()
            if user:
                self._signed_in_user = user
                self.setWindowTitle(f"JetFyx — {self._signed_in_user}")
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
        self.chart_widget = TradingChartPlugin()
        self.setCentralWidget(self.chart_widget)

    def _setup_theme_toolbar_button(self):
        """
        Move the palette/theme action to the far RIGHT of the toolbar
        by removing it from its current position, adding an expanding
        spacer widget, then re-adding the action at the end.
        """
        try:
            from PySide6.QtWidgets import QWidget as _QWidget, QSizePolicy as _QSP, QToolButton as _QTB
            tb = self.ui.toolBar

            # Remove existing actiontheme from wherever it currently sits
            tb.removeAction(self.ui.actiontheme)

            # Expanding spacer pushes everything after it to the right
            spacer = _QWidget(self)
            spacer.setSizePolicy(_QSP.Expanding, _QSP.Preferred)
            spacer.setObjectName("toolbar_spacer")
            tb.addWidget(spacer)

            # Re-add theme action at the far right
            tb.addAction(self.ui.actiontheme)

            # Connect directly (safe to call multiple times – Qt deduplicates)
            try:
                self.ui.actiontheme.triggered.disconnect()
            except Exception:
                pass
            self.ui.actiontheme.triggered.connect(self.open_theme_popup)
        except Exception as e:
            logging.getLogger(__name__).debug("Could not move theme button: %s", e)

    def _connect_actions(self):
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionOpen_an_Account.triggered.connect(self._open_login_dialog)

        # Move theme icon to rightmost toolbar position and connect it
        self._setup_theme_toolbar_button()

        # Also wire View menu if the action exists in the .ui file
        try:
            self.ui.actionTheme_Settings.triggered.connect(self.open_theme_popup)
        except Exception:
            pass
        # Add dynamically to View menu (shows "Theme Settings" menu item)
        try:
            theme_action = QAction("Theme Settings", self)
            theme_action.triggered.connect(self.open_theme_popup)
            self.ui.menuView.addAction(theme_action)
        except Exception:
            pass

    def open_theme_popup(self):
        """Show / hide the theme settings slide-in popup."""
        if self._theme_popup is not None:
            self._theme_popup.toggle_popup()

    def _create_orders_dock(self):
        """Create and dock the Orders panel. Safe to call multiple times."""
        logging.getLogger(__name__).info("_create_orders_dock() called")

        if getattr(self, 'orders_dock', None) is not None:
            return

        try:
            from Orders.ui.order_dock import OrderDock
            from PySide6.QtWidgets import QDockWidget
            from PySide6.QtCore import Qt

            self.orders_dock = OrderDock(
                parent=self,
                order_service=getattr(self, 'order_service', None)
            )

            logging.getLogger(__name__).info(
                "OrderDock instance created: %s", repr(self.orders_dock)
            )

            # Try normal docking
            try:
                self.addDockWidget(Qt.BottomDockWidgetArea, self.orders_dock)

                try:
                    self.setDockOptions(
                        QMainWindow.AllowTabbedDocks
                        | QMainWindow.AllowNestedDocks
                        | QMainWindow.AnimatedDocks
                    )
                except Exception:
                    pass

                try:
                    self.orders_dock.setFloating(False)
                    self.orders_dock.raise_()
                except Exception:
                    pass

            except Exception:
                # Fallback if addDockWidget fails
                try:
                    self.orders_dock.setParent(self)
                    self.orders_dock.setFloating(False)
                    self.orders_dock.show()
                except Exception:
                    pass

            self.orders_widget = None

            # Configure dock features
            try:
                self.orders_dock.setFeatures(
                    QDockWidget.DockWidgetClosable
                    | QDockWidget.DockWidgetMovable
                    | QDockWidget.DockWidgetFloatable
                )
                self.orders_dock.setFloating(False)
                self.orders_dock.setMinimumHeight(120)
            except Exception:
                logging.exception("Failed to configure Orders dock features")

            # Create View → Orders menu action
            try:
                self.ui.actionOrders = QAction("Orders", self)
                self.ui.actionOrders.setCheckable(True)
                self.ui.menuView.addAction(self.ui.actionOrders)

                self.ui.actionOrders.setChecked(self.orders_dock.isVisible())
                self.ui.actionOrders.toggled.connect(self.orders_dock.setVisible)
                self.orders_dock.visibilityChanged.connect(
                    lambda v: self.ui.actionOrders.setChecked(v)
                )
            except Exception:
                logging.exception("Failed to create Orders view action")

            # Debug info
            try:
                print("Orders dock visible:", self.orders_dock.isVisible())
                print("Orders dock area:", self.dockWidgetArea(self.orders_dock))
                print("Orders dock geometry:", self.orders_dock.geometry())
            except Exception:
                logging.exception("Failed to print Orders dock debug info")

        except Exception:
            logging.exception("Failed to create Orders dock")


    # ---------------- LOGIN DIALOG ----------------

    def _open_login_dialog(self):
        # Prefer the AccountsWidget login flow if the left panel is present
        try:
            if hasattr(self, 'accounts_widget') and self.accounts_widget is not None:
                print("[DEBUG] Using AccountsWidget.show_login()")
                # AccountsWidget.show_login will manage building the accounts tree
                self.accounts_widget.show_login()

                # Update main window state from persisted session/store
                try:
                    user = session.get_current_user()
                    if user:
                        self._on_login_success(user)
                except Exception:
                    pass
                return
        except Exception:
            pass

        # Fallback: use the top-level Login dialog as before
        print("[DEBUG] Using fallback LoginPage from Main_window")
        self.login_dialog = LoginPage(self)
        self.login_dialog.login_success.connect(self._on_login_success)
        # Open the forgot password dialog when login page emits the signal
        try:
            from Create_Account import CreateAccountDialog
            self.login_dialog.create_account_requested.connect(self._open_create_account_dialog)
            print("[DEBUG] Connected create_account_requested in Main_window fallback")
            try:
                # Connect forgot password signal if available
                self.login_dialog.forgot_password_requested.connect(self._open_forgot_dialog)
            except Exception:
                pass
        except Exception as e:
            # keep behavior tolerant if module not present
            print(f"[DEBUG] Failed to connect create_account_requested in fallback: {e}")
            pass
        self.login_dialog.exec()

    def _open_create_account_dialog(self):
        print("[DEBUG] _open_create_account_dialog() called in Main_window")
        try: 
            from Create_Account import CreateAccountDialog
            print(f"[DEBUG] CreateAccountDialog imported: {CreateAccountDialog}")
            d = CreateAccountDialog(self)
            print(f"[DEBUG] Created CreateAccountDialog instance: {d}")
            result = d.exec()
            print(f"[DEBUG] CreateAccountDialog.exec() returned: {result}")
        except Exception as e:
            print(f"[DEBUG] Error in _open_create_account_dialog: {e}")
            import traceback
            traceback.print_exc()

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
            try:
                self.ui.menuFile.addAction(self._sign_out_action)
            except Exception:
                self.menuBar().addAction(self._sign_out_action)

        # Optionally disable the login action while signed in
        try:
            self.ui.actionOpen_an_Account.setEnabled(False)
        except Exception:
            pass
        # Ensure left panel dock is visible when user signs in
        try:
            if hasattr(self, 'left_panel_dock') and self.left_panel_dock is not None:
                self.left_panel_dock.setVisible(True)
                try:
                    self.ui.actionMarket_Watch.setChecked(True)
                except Exception:
                    pass
        except Exception:
            pass
        # Create Orders dock now that the user is authenticated
        try:
            self._create_orders_dock()
        except Exception:
            pass
        # Ensure orders dock is visible when user signs in
        try:
            if hasattr(self, 'orders_dock') and self.orders_dock is not None:
                self.orders_dock.setVisible(True)
                try:
                    # Keep the View menu action in sync if present
                    if hasattr(self.ui, 'actionOrders'):
                        self.ui.actionOrders.setChecked(True)
                except Exception:
                    pass
        except Exception:
            pass
        # If left panel MarketWidget exists, set its active account from the store so
        # it can fetch favourite/watchlist symbols immediately.
        try:
            from accounts.store import AppStore
            store = AppStore.instance()
            cur = store.get_current_account()
            acct_id = cur.get('account_id') or cur.get('accountId') or None
            if acct_id and hasattr(self, 'left_panel_widget') and getattr(self.left_panel_widget, 'market_widget', None):
                try:
                    self.left_panel_widget.market_widget.set_account_id(acct_id)
                except Exception:
                    pass
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

        # Re-enable login action
        try:
            self.ui.actionOpen_an_Account.setEnabled(True)
        except Exception:
            pass
        # Hide left panel dock on sign out
        try:
            if hasattr(self, 'left_panel_dock') and self.left_panel_dock is not None:
                self.left_panel_dock.setVisible(False)
                try:
                    self.ui.actionMarket_Watch.setChecked(False)
                except Exception:
                    pass
        except Exception:
            pass
        # Hide orders dock on sign out
        try:
            if hasattr(self, 'orders_dock') and self.orders_dock is not None:
                self.orders_dock.setVisible(False)
                try:
                    if hasattr(self.ui, 'actionOrders'):
                        self.ui.actionOrders.setChecked(False)
                except Exception:
                    pass
        except Exception:
            pass
        # Remove and delete the orders dock to mirror left panel cleanup
        try:
            if hasattr(self, 'orders_dock') and self.orders_dock is not None:
                try:
                    if hasattr(self.ui, 'actionOrders'):
                        try:
                            self.ui.menuView.removeAction(self.ui.actionOrders)
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self.removeDockWidget(self.orders_dock)
                except Exception:
                    pass
                try:
                    self.orders_dock.deleteLater()
                except Exception:
                    pass
                self.orders_dock = None
                self.orders_widget = None
                try:
                    delattr(self.ui, 'actionOrders')
                except Exception:
                    pass
        except Exception:
            pass

    def _on_market_watch_visibility_changed(self, visible):
        """Update the action checked state when dock visibility changes."""
        self.ui.actionMarket_Watch.setChecked(visible)

    def resizeEvent(self, event):
        """Adjust left panel dock preferred width proportionally on resize.

        Keeps a sensible minimum and maximum so the dock expands to occupy
        a large portion of the window without overlapping important central UI.
        """
        try:
            if hasattr(self, 'left_panel_dock') and self.left_panel_dock is not None:
                total_w = max(1, self.width())
                # Preferred: 35% of window width, clamp between 300 and 70%
                pref = max(300, int(total_w * 0.25))
                max_w = max(pref, int(total_w * 0.7))
                try:
                    self.left_panel_dock.setMinimumWidth(pref)
                except Exception:
                    pass
                try:
                    self.left_panel_dock.setMaximumWidth(max_w)
                except Exception:
                    pass
        except Exception:
            pass

        return super().resizeEvent(event)