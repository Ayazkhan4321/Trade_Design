# Networking for inbox fetch
import requests
from accounts.store import AppStore
import auth.session as session
from api.config import API_CLIENT_MESSAGES_ACCOUNT, API_TIMEOUT, API_VERIFY_TLS

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabBar, QStackedLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from .orders_tab import OrdersTab
from .history_table import HistoryTable
from .inbox_table import InboxTable
# Placeholder for other tabs
from PySide6.QtWidgets import QLabel
from Orders.services.order_updates_service import OrderUpdatesService
import logging

LOG = logging.getLogger(__name__)


class OrdersWidget(QWidget):
    """Widget version of the Orders UI so it can be embedded in docks.

    Kept as a single-file component exposing the same API as the old
    `MainWindow` for minimal changes elsewhere.
    """
    def __init__(self, parent=None, order_service=None):
        super().__init__(parent)
        self.setWindowTitle("Order Desk")
        self.resize(1200, 700)  # start size
        
        # Initialize OrderUpdatesService (will be connected after account is loaded)
        self.order_updates_service = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header buttons (will be placed on the same row as tabs)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(34, 34)
        self.settings_btn.setStyleSheet("border:none; background: transparent; font-size:16px;")
        self.settings_btn.setObjectName("OrdersSettingsBtn")
        try:
            self.settings_btn.setCursor(Qt.PointingHandCursor)
        except Exception:
            pass
        self.funnel_btn = QPushButton("⏷")
        self.funnel_btn.setFixedSize(34, 34)
        self.funnel_btn.setStyleSheet("border:none; background: transparent; font-size:14px;")
        self.funnel_btn.setObjectName("OrdersFunnelBtn")

        # Use a QTabBar in the top row and a QStackedLayout for pages below
        self.tabbar = QTabBar(self)
        self.tabbar.setObjectName("OrdersTabBar")
        self.tabbar.addTab("Order")
        self.tabbar.addTab("History")
        self.tabbar.addTab("Inbox")
        self.tabbar.addTab("Logs")
        self.tabbar.setExpanding(False)

        # Widget object name for scoped stylesheet
        try:
            self.setObjectName("OrdersWidget")
        except Exception:
            pass

        # Scoped stylesheet for header/tab appearance matching the design
        try:
            self.setStyleSheet("""
QWidget#OrdersWidget { background: #ffffff; }
QTabBar#OrdersTabBar { background: transparent; padding: 0px 0px; }
QTabBar#OrdersTabBar::tab { background: #f5f5f5; border: none; border-bottom: 3px solid transparent; padding: 8px 16px; margin-right: 0px; color: #666; font-size: 12px; font-weight: 600; }
QTabBar#OrdersTabBar::tab:selected { background: #ffffff; color: #1976d2; border-bottom: 3px solid #1976d2; }
QTabBar#OrdersTabBar::tab:hover { background: #e8e8e8; }
QLabel#OrdersTitle { color: #1976d2; font-weight: 600; padding-left: 12px; padding-right: 12px; }
QPushButton#OrdersSettingsBtn, QPushButton#OrdersFunnelBtn { background: transparent; border: none; color: #666; }
QPushButton#OrdersSettingsBtn:hover, QPushButton#OrdersFunnelBtn:hover { background: #e8e8e8; border-radius: 3px; }
""")
        except Exception:
            pass

        self.orders_tab = OrdersTab(order_service=order_service)
        self.history_tab = HistoryTable()
        self.inbox_tab = InboxTable()
        self.logs_tab = QLabel("Logs Tab")

        # Stacked layout to hold the actual pages
        self.stack = QStackedLayout()
        self.stack.addWidget(self.orders_tab)
        self.stack.addWidget(self.history_tab)
        self.stack.addWidget(self.inbox_tab)
        self.stack.addWidget(self.logs_tab)

        # Top row with tabbar (left) and buttons (right)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        # Left: tabs
        top_row.addWidget(self.tabbar)

        # Center: title label (centered via stretches)
        try:
            top_row.addStretch()
            self.title_label = QLabel("Order Desk")
            self.title_label.setObjectName("OrdersTitle")
            self.title_label.setStyleSheet("color: #1e63d6; font-weight: 600; padding-left: 40px; padding-right: 40px;")
            self.title_label.setAlignment(Qt.AlignCenter)
            top_row.addWidget(self.title_label)
            top_row.addStretch()
        except Exception:
            pass

        btns_layout = QHBoxLayout()
        btns_layout.setContentsMargins(6, 0, 6, 0)
        btns_layout.addWidget(self.settings_btn)
        btns_layout.addWidget(self.funnel_btn)
        top_row.addStretch()
        top_row.addLayout(btns_layout)
        main_layout.addLayout(top_row)

        # Add the stacked pages below the top row
        main_layout.addLayout(self.stack)

        # Connect tab change signal
        try:
            self.tabbar.currentChanged.connect(lambda idx: self.on_tab_changed(self.tabbar.tabText(idx)))
            # Buttons: OrderDock will connect to these directly; keep wiring local for convenience
            self.settings_btn.clicked.connect(lambda: self.on_tab_changed(self.tabbar.tabText(self.tabbar.currentIndex())))
            self.funnel_btn.clicked.connect(lambda: self.on_tab_changed(self.tabbar.tabText(self.tabbar.currentIndex())))
        except Exception:
            pass

        # If an OrderService is provided, register a listener so new orders
        # created elsewhere (trade panel / dialog) can be injected into the
        # local table model.
        try:
            if order_service is not None:
                order_service.register_listener(self._on_order_created)
                # keep a reference for potential future use
                self.order_service = order_service
                LOG.debug("OrdersWidget registered listener with OrderService %s", repr(order_service))
                # Fetch existing orders from backend and populate the table
                try:
                    orders = []
                    try:
                        orders = order_service.fetch_orders()
                    except Exception:
                        # Fallback to any cached active orders
                        orders = order_service.get_active_orders()

                    model = getattr(self.orders_tab, 'table').model
                    for o in orders:
                        try:
                            model.add_order(o)
                        except Exception:
                            LOG.exception("Failed adding fetched order to model: %s", o)
                    LOG.info("OrdersWidget populated table with fetched orders: %s", len(orders))
                    
                    # Initialize OrderUpdatesService now that we have an account context
                    QTimer.singleShot(200, self._connect_order_updates)
                except Exception:
                    LOG.exception("Failed to fetch/populate existing orders on init")
        except Exception:
            LOG.exception("Failed to register OrdersWidget listener with OrderService")

        # Initial tab (emit happened in TopBar init; ensure UI consistent)
        try:
            # Ensure initial tab loads (Orders by default)
            self.on_tab_changed("Order")
        except Exception:
            pass

        # Defer connecting to market price updates until widget is parented in the
        # main window so we can locate the application's SymbolManager instance.
        try:
            QTimer.singleShot(0, self._connect_price_updates)
        except Exception:
            pass
        
        # Connect to account changes to initialize OrderUpdatesService
        try:
            from accounts.store import AppStore
            store = AppStore()
            store.account_changed.connect(self._on_account_changed_for_orders)
            # Connect to account_id_changed if signal exists (it will exist after login)
            if hasattr(store, 'account_id_changed'):
                store.account_id_changed.connect(self._on_account_id_changed)
                LOG.debug("OrdersWidget connected to store.account_id_changed signal")
            LOG.debug("OrdersWidget connected to store.account_changed")
        except Exception:
            LOG.exception("Failed to connect to account signals")

    def switch_tab(self, index):
        try:
            # switch the displayed page: prefer the stacked layout, fall back to tabwidget
            if hasattr(self, 'stack') and self.stack is not None:
                try:
                    self.stack.setCurrentIndex(index)
                    return
                except Exception:
                    pass
            if hasattr(self, 'tabwidget'):
                self.tabwidget.setCurrentIndex(index)
        except Exception:
            pass

    def on_tab_changed(self, name: str):
        # Normalize the incoming name and switch stacked layout
        base = name.split("(")[0].strip()
        mapping = {
            "Order": 0,
            "History": 1,
            "Inbox": 2,
            "Logs": 3,
        }
        idx = mapping.get(base, 0)
        self.switch_tab(idx)
        # Update settings / funnel button visibility to follow previous TopBar rules
        try:
            base = name.split("(")[0].strip()
            if base in ("Order", "History"):
                try:
                    self.settings_btn.show()
                except Exception:
                    pass
            else:
                try:
                    self.settings_btn.hide()
                except Exception:
                    pass

            if base in ("History", "Logs"):
                try:
                    self.funnel_btn.show()
                except Exception:
                    pass
            else:
                try:
                    self.funnel_btn.hide()
                except Exception:
                    pass
        except Exception:
            pass

        # If History was selected, attempt to populate the history table
        try:
            if base == 'History':
                # Use registered OrderService if available
                svc = getattr(self, 'order_service', None)
                hist_widget = getattr(self.history_tab, 'set_rows', None)
                if svc is not None and callable(getattr(svc, 'fetch_history', None)) and callable(hist_widget):
                    try:
                        rows = svc.fetch_history()
                        # Feed rows into the history widget
                        self.history_tab.set_rows(rows)
                    except Exception:
                        LOG.exception('Failed populating history tab')
            # If Inbox was selected, fetch messages for current account and populate
            try:
                if base == 'Inbox':
                    try:
                        store = AppStore.instance()
                        current = store.get_current_account() or {}
                        account_id = current.get('account_id') or current.get('accountNumber') or current.get('account_number')
                        if not account_id:
                            LOG.warning("Inbox selected but no current account id available")
                        else:
                            url = API_CLIENT_MESSAGES_ACCOUNT.format(accountId=account_id)
                            headers = {}
                            token = session.get_token()
                            if token:
                                headers['Authorization'] = f"Bearer {token}"
                            # Add referer to match backend expectations if available
                            try:
                                headers['Referer'] = "https://jetwebapp"
                            except Exception:
                                pass

                            params = {"pageNumber": 1, "pageSize": 25}
                            LOG.debug("Fetching inbox messages: %s params=%s", url, params)
                            try:
                                resp = requests.get(url, headers=headers, params=params, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
                                LOG.debug("Inbox fetch status: %s", getattr(resp, 'status_code', None))
                                try:
                                    payload = resp.json()
                                except Exception:
                                    payload = None

                                # Normalise payload into list of rows for InboxTable.set_rows
                                rows = []
                                # Common patterns: either direct list, or { 'data': [...]} or { 'items': [...]} or { 'result': [...]}
                                candidates = None
                                if isinstance(payload, list):
                                    candidates = payload
                                elif isinstance(payload, dict):
                                    for k in ('data', 'items', 'result', 'messages'):
                                        if isinstance(payload.get(k), list):
                                            candidates = payload.get(k)
                                            break
                                    # If no list found, but payload has a top-level 'data' object with 'items'
                                    if candidates is None and isinstance(payload.get('data'), dict) and isinstance(payload['data'].get('items'), list):
                                        candidates = payload['data']['items']

                                if candidates is None:
                                    LOG.debug("Inbox fetch returned unexpected payload: %s", type(payload))
                                    candidates = []

                                # Map candidate items to expected keys
                                for it in candidates:
                                    if not isinstance(it, dict):
                                        continue
                                    subj = it.get('subject') or it.get('title') or it.get('messageSubject') or ''
                                    sender = it.get('fromAddress') or it.get('from') or it.get('sender') or it.get('createdBy') or ''
                                    time = it.get('createdAt') or it.get('sentAt') or it.get('time') or it.get('date') or ''
                                    rows.append({'subject': subj, 'from': sender, 'time': time, 'actions': ''})

                                try:
                                    if hasattr(self.inbox_tab, 'set_rows'):
                                        self.inbox_tab.set_rows(rows)
                                        LOG.info("Inbox populated with %s messages", len(rows))
                                except Exception:
                                    LOG.exception("Failed to set inbox rows")
                            except Exception:
                                LOG.exception("Failed to fetch inbox messages from %s", url)
                    except Exception:
                        LOG.exception("Inbox selection handler failed")
            except Exception:
                pass
        except Exception:
            pass

    def _on_order_created(self, order: dict):
        """Callback from OrderService when a new order is created remotely.

        Converts the incoming order dict into the model's expected keys and
        appends it to the Orders table.
        """
        try:
            LOG.info("OrdersWidget._on_order_created called: %s", order)
            model = getattr(self.orders_tab, 'table').model

            # Some notifications are close events: { 'id': <id>, 'closed': True, 'payload': {...} }
            if isinstance(order, dict) and order.get('closed'):
                # Determine id from either top-level or payload
                oid = order.get('id') or (order.get('payload') or {}).get('id')
                if oid is None:
                    LOG.warning("Close notification received without id: %s", order)
                    return
                removed = False
                try:
                    removed = model.remove_order_by_id(oid)
                except Exception:
                    LOG.exception("Failed removing closed order id=%s", oid)
                if removed:
                    LOG.info("OrdersWidget removed closed order id=%s from model", oid)
                else:
                    LOG.debug("OrdersWidget did not find order id=%s to remove", oid)
                return

            # Normalize keys expected by OrderModel for new orders
            norm = {
                'id': order.get('id', 0),
                'time': order.get('time') or order.get('createdAt') or '',
                'type': order.get('type') or order.get('orderType') or '',
                'symbol': order.get('symbol', ''),
                'lot': order.get('lot') or order.get('lotSize') or order.get('volume') or 0,
                'entry_price': order.get('entry_price') or order.get('entryPriceForPendingOrder') or 0,
                'entry_value': order.get('entry_value', 0),
                'sl': order.get('stopLoss', 0),
                'tp': order.get('takeProfit', 0),
                'market_price': order.get('market_price', 0),
                'market_value': order.get('market_value', 0),
                'swap': order.get('swap', 0),
                'commission': order.get('commission', 0),
                'pl': order.get('pl', 0),
                'pl_pct': order.get('pl_pct', 0),
                'remarks': order.get('remark', order.get('remarks', '')),
            }
            model.add_order(norm)
            LOG.info("OrdersWidget forwarded order to model: id=%s symbol=%s", norm.get('id'), norm.get('symbol'))
            
            # Initialize OrderUpdatesService if not already done (triggered by first order)
            if self.order_updates_service is None:
                QTimer.singleShot(0, self._connect_order_updates)
        except Exception:
            LOG.exception("OrdersWidget failed to handle created order: %s", order)

    def _connect_price_updates(self):
        """Locate the app's SymbolManager (if present) and subscribe to price updates."""
        try:
            main = self.window()
            if not main:
                return
            # MainWindow keeps `left_panel_widget` when the Left Panel is present
            lp = getattr(main, 'left_panel_widget', None)
            market = None
            if lp is not None and hasattr(lp, 'market_widget'):
                market = getattr(lp, 'market_widget')

            # Also allow direct attribute if main has market_widget
            if market is None and hasattr(main, 'market_widget'):
                market = getattr(main, 'market_widget')

            if market is None:
                LOG.debug("OrdersWidget: no MarketWidget found to subscribe price updates")
                return

            symbol_manager = getattr(market, 'symbol_manager', None)
            if symbol_manager is None:
                LOG.debug("OrdersWidget: MarketWidget has no symbol_manager")
                return

            try:
                symbol_manager.priceUpdated.connect(self._on_price_tick)
                LOG.debug("OrdersWidget connected to SymbolManager.priceUpdated")
            except Exception:
                LOG.exception("Failed to connect OrdersWidget to SymbolManager.priceUpdated")
        except Exception:
            LOG.exception("_connect_price_updates failed")

    def _on_price_tick(self, symbol, sell, buy):
        """Handle live price ticks: update model and bottom Net P&L."""
        try:
            model = getattr(self.orders_tab, 'table').model
            model.update_market_price(symbol, sell, buy)

            # Recompute net P/L and update bottom bar
            try:
                total = sum([float(o.get('pl') or 0.0) for o in model.orders])
            except Exception:
                total = 0.0
            try:
                bottom = getattr(self.orders_tab.table, 'bottom_bar', None)
                if bottom is not None:
                    bottom.set_net_pl(total)
            except Exception:
                LOG.exception("Failed updating bottom Net P&L")
        except Exception:
            LOG.exception("_on_price_tick failed for %s", symbol)

    def _on_account_changed_for_orders(self, account_info: dict):
        """Handle account changes: disconnect old service and connect new one."""
        try:
            account_id = account_info.get('account_id') or account_info.get('accountId')
            if not account_id:
                LOG.debug("OrdersWidget._on_account_changed_for_orders: No account ID in account_info")
                return
            
            # Disconnect old service if it exists
            if self.order_updates_service is not None:
                try:
                    self.order_updates_service.disconnect()
                    LOG.info("OrdersWidget: Disconnected previous OrderUpdatesService")
                except Exception:
                    LOG.exception("Error disconnecting previous OrderUpdatesService")
            
            # Initialize new service for this account
            LOG.info("OrdersWidget: Account changed to %s, initializing OrderUpdatesService", account_id)
            self._connect_order_updates(account_id)
            
        except Exception:
            LOG.exception("Error handling account change in OrdersWidget")

    def _on_account_id_changed(self, account_id: int):
        """Handle account_id signal directly from store for simpler OrderUpdatesService initialization."""
        try:
            LOG.info("OrdersWidget._on_account_id_changed: account_id=%s", account_id)
            
            # Disconnect old service if it exists
            if self.order_updates_service is not None:
                try:
                    self.order_updates_service.disconnect()
                    LOG.debug("OrdersWidget: Disconnected previous OrderUpdatesService for re-initialization")
                except Exception:
                    LOG.exception("Error disconnecting previous OrderUpdatesService")
            
            # Initialize new service with the account_id from the signal
            self._connect_order_updates(account_id)
            
        except Exception:
            LOG.exception("Error handling account_id change in OrdersWidget")

    def _connect_order_updates(self, account_id=None):
        """Initialize and connect OrderUpdatesService for real-time P&L updates.
        
        Args:
            account_id: The account ID to connect for. If None, tries to get from store.
        """
        try:
            # Skip if already connected
            if self.order_updates_service is not None and self.order_updates_service.is_connected():
                LOG.debug("OrderUpdatesService already connected, skipping re-initialization")
                return
            
            # Get account ID if not provided
            if not account_id:
                try:
                    store = AppStore()
                    current_account = store.get_current_account() or {}
                    account_id = current_account.get('account_id') or current_account.get('accountId')
                except Exception:
                    pass
            
            # Last resort fallback: try to extract from order_service or model
            if not account_id:
                try:
                    if hasattr(self, 'order_service') and self.order_service and hasattr(self.order_service, '_last_account_id'):
                        account_id = self.order_service._last_account_id
                except Exception:
                    pass
            
            if not account_id:
                LOG.debug("OrdersWidget._connect_order_updates: No account ID available")
                return
            
            LOG.info("OrdersWidget._connect_order_updates: Starting for account %s", account_id)
            
            # Create and connect OrderUpdatesService
            self.order_updates_service = OrderUpdatesService(account_id=account_id)
            
            # Connect order update signals to model
            model = getattr(self.orders_tab, 'table', None)
            if model is None:
                LOG.warning("OrdersWidget._connect_order_updates: Could not find orders table")
                return
            
            model = getattr(model, 'model', None)
            if model is None:
                LOG.warning("OrdersWidget._connect_order_updates: Could not find order model")
                return
            
            # Connect signals
            self.order_updates_service.orderUpdated.connect(
                lambda order_data: model.update_order_from_backend(order_data)
            )
            self.order_updates_service.orderCreated.connect(
                lambda order_data: model.add_order(order_data)
            )
            self.order_updates_service.orderClosed.connect(
                lambda order_id: model.remove_order_by_id(order_id)
            )
            self.order_updates_service.connectionStatusChanged.connect(self._on_order_updates_connection_changed)
            
            LOG.debug("OrdersWidget connected OrderUpdatesService signals")
            
            # Start the connection
            self.order_updates_service.connect()
            LOG.info("OrdersWidget started OrderUpdatesService")
            
        except Exception:
            LOG.exception("Failed to initialize OrderUpdatesService")

    def _on_order_updates_connection_changed(self, is_connected):
        """Handle OrderUpdatesService connection status changes."""
        status = "CONNECTED" if is_connected else "DISCONNECTED"
        LOG.info("[OrderUpdatesService] Connection status changed: %s", status)

# Backwards compatibility: expose a clear name for the Orders entry point
OrdersMainWindow = OrdersWidget
