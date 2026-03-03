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
from PySide6.QtWidgets import QLabel
from Orders.services.order_updates_service import OrderUpdatesService
import logging

LOG = logging.getLogger(__name__)


class OrdersWidget(QWidget):
    """Widget version of the Orders UI so it can be embedded in docks."""

    def __init__(self, parent=None, order_service=None):
        super().__init__(parent)
        self.setWindowTitle("Order Desk")
        self.resize(1200, 700)

        self.order_updates_service = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Buttons — objectNames required so parent stylesheet rules match ──
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("OrdersSettingsBtn")   # FIX: was missing
        self.settings_btn.setFixedSize(32, 32)
        try:
            self.settings_btn.setCursor(Qt.PointingHandCursor)
        except Exception:
            pass

        self.funnel_btn = QPushButton("⏷")
        self.funnel_btn.setObjectName("OrdersFunnelBtn")       # FIX: was missing
        self.funnel_btn.setFixedSize(32, 32)

        # ── Tab bar ────────────────────────────────────────────────────────
        self.tabbar = QTabBar(self)
        self.tabbar.setObjectName("OrdersTabBar")
        self.tabbar.addTab("Order")
        self.tabbar.addTab("History")
        self.tabbar.addTab("Inbox")
        self.tabbar.addTab("Logs")
        self.tabbar.setExpanding(False)

        self.setObjectName("OrdersWidget")

        # ── Tab pages ─────────────────────────────────────────────────────
        self.orders_tab  = OrdersTab(order_service=order_service)
        self.history_tab = HistoryTable()
        self.inbox_tab   = InboxTable()
        self.logs_tab    = QLabel("Logs Tab")

        self.stack = QStackedLayout()
        self.stack.addWidget(self.orders_tab)
        self.stack.addWidget(self.history_tab)
        self.stack.addWidget(self.inbox_tab)
        self.stack.addWidget(self.logs_tab)

        # ── Top row ────────────────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        top_row.addWidget(self.tabbar)

        try:
            top_row.addStretch()
            self.title_label = QLabel("Order Desk")
            self.title_label.setObjectName("OrdersTitle")
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
        main_layout.addLayout(self.stack)

        # ── Initial theme paint ───────────────────────────────────────────
        # FIX: was a one-shot inline block; now a proper method called here
        # AND re-called on every theme_changed signal.
        self._apply_styles(self._get_tokens())

        # ── Live theme updates ────────────────────────────────────────────
        # FIX: OrdersWidget never connected to theme_changed — this is the
        # root cause of the stale colour bug.  The lambda is stored as an
        # instance attribute so PySide6 doesn't GC the connection.
        try:
            from Theme.theme_manager import ThemeManager
            self._on_theme_changed = lambda name, tokens: self._apply_styles(tokens)
            ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
        except Exception:
            pass

        # ── Tab signal ────────────────────────────────────────────────────
        try:
            self.tabbar.currentChanged.connect(
                lambda idx: self.on_tab_changed(self.tabbar.tabText(idx))
            )
        except Exception:
            pass

        # ── Order service ─────────────────────────────────────────────────
        try:
            if order_service is not None:
                order_service.register_listener(self._on_order_created)
                self.order_service = order_service
                LOG.debug("OrdersWidget registered listener with OrderService %s", repr(order_service))
                try:
                    orders = []
                    try:
                        orders = order_service.fetch_orders()
                    except Exception:
                        orders = order_service.get_active_orders()

                    model = getattr(self.orders_tab, 'table').model
                    for o in orders:
                        try:
                            model.add_order(o)
                        except Exception:
                            LOG.exception("Failed adding fetched order to model: %s", o)
                    LOG.info("OrdersWidget populated table with %s orders", len(orders))
                    QTimer.singleShot(200, self._connect_order_updates)
                except Exception:
                    LOG.exception("Failed to fetch/populate existing orders on init")
        except Exception:
            LOG.exception("Failed to register OrdersWidget listener with OrderService")

        try:
            self.on_tab_changed("Order")
        except Exception:
            pass

        try:
            QTimer.singleShot(0, self._connect_price_updates)
        except Exception:
            pass

        try:
            from accounts.store import AppStore
            store = AppStore()
            store.account_changed.connect(self._on_account_changed_for_orders)
            if hasattr(store, 'account_id_changed'):
                store.account_id_changed.connect(self._on_account_id_changed)
                LOG.debug("OrdersWidget connected to store.account_id_changed signal")
            LOG.debug("OrdersWidget connected to store.account_changed")
        except Exception:
            LOG.exception("Failed to connect to account signals")

    # ------------------------------------------------------------------ #
    # Theme helpers                                                         #
    # ------------------------------------------------------------------ #

    def _get_tokens(self) -> dict:
        try:
            from Theme.theme_manager import ThemeManager
            return ThemeManager.instance().tokens()
        except Exception:
            return {}

    def _apply_styles(self, tokens: dict):
        """Apply the full widget stylesheet from *tokens*.

        Called at init AND on every theme_changed signal so the tab bar
        and buttons always reflect the current accent colour.

        All rules live in ONE self.setStyleSheet() call using objectName
        selectors — resolved before the app stylesheet and applied
        atomically (no cleared-then-reset race window).  Children must
        carry no widget-level stylesheet of their own.
        """
        t = tokens if tokens else {}

        bg_w   = t.get("bg_widget",        "#ffffff")
        tab_i  = t.get("bg_tab_inactive",  "transparent")
        tab_a  = t.get("bg_tab_active",    "#e6f0ff")
        tab_h  = t.get("bg_button_hover",  "#e2e8f0")
        col_i  = t.get("text_tab_inactive","#6b7280")
        col_a  = t.get("text_tab_active",  "#1976d2")
        acc    = t.get("accent",           "#1976d2")
        text_p = t.get("text_primary",     "#1a202c")

        self.setStyleSheet(f"""
            QWidget#OrdersWidget {{
                background: {bg_w};
            }}

            QTabBar#OrdersTabBar {{
                background: transparent;
                padding: 0px;
            }}
            QTabBar#OrdersTabBar::tab {{
                background: {tab_i};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                margin-right: 0px;
                color: {col_i};
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar#OrdersTabBar::tab:selected {{
                background: {tab_a};
                color: {col_a};
                border-bottom: 3px solid {acc};
            }}
            QTabBar#OrdersTabBar::tab:hover {{
                background: {tab_h};
                color: {text_p};
            }}

            QLabel#OrdersTitle {{
                color: {col_a};
                font-weight: 600;
                padding-left: 12px;
                padding-right: 12px;
            }}

            QPushButton#OrdersSettingsBtn,
            QPushButton#OrdersFunnelBtn {{
                background: transparent;
                color: {text_p};
                border: none;
                font-family: "Segoe UI", "Inter", "Arial", sans-serif;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton#OrdersSettingsBtn:hover,
            QPushButton#OrdersFunnelBtn:hover {{
                background: {tab_h};
                color: {acc};
                border-radius: 4px;
            }}
            QPushButton#OrdersSettingsBtn:pressed,
            QPushButton#OrdersFunnelBtn:pressed {{
                background: {tab_a};
                color: {acc};
                border-radius: 4px;
            }}
        """)

        # Wipe any stale widget-level stylesheets on children so the
        # parent's rules above are not shadowed.
        self.tabbar.setStyleSheet("")
        self.settings_btn.setStyleSheet("")
        self.funnel_btn.setStyleSheet("")

    def closeEvent(self, event):
        """Disconnect theme listener to avoid dangling reference."""
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.disconnect(self._on_theme_changed)
        except Exception:
            pass
        super().closeEvent(event)

    # ------------------------------------------------------------------ #
    # Tab / button logic (unchanged from original)                          #
    # ------------------------------------------------------------------ #

    def switch_tab(self, index):
        try:
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
        base = name.split("(")[0].strip()
        mapping = {"Order": 0, "History": 1, "Inbox": 2, "Logs": 3}
        idx = mapping.get(base, 0)
        self.switch_tab(idx)

        try:
            self.settings_btn.setVisible(base in ("Order", "History"))
            self.funnel_btn.setVisible(base in ("History", "Logs"))
        except Exception:
            pass

        try:
            if base == 'History':
                svc = getattr(self, 'order_service', None)
                hist_widget = getattr(self.history_tab, 'set_rows', None)
                if svc is not None and callable(getattr(svc, 'fetch_history', None)) and callable(hist_widget):
                    try:
                        rows = svc.fetch_history()
                        self.history_tab.set_rows(rows)
                    except Exception:
                        LOG.exception('Failed populating history tab')

            if base == 'Inbox':
                try:
                    store = AppStore.instance()
                    current = store.get_current_account() or {}
                    account_id = (current.get('account_id') or
                                  current.get('accountNumber') or
                                  current.get('account_number'))
                    if not account_id:
                        LOG.warning("Inbox selected but no current account id available")
                    else:
                        url = API_CLIENT_MESSAGES_ACCOUNT.format(accountId=account_id)
                        headers = {}
                        token = session.get_token()
                        if token:
                            headers['Authorization'] = f"Bearer {token}"
                        try:
                            headers['Referer'] = "https://jetwebapp"
                        except Exception:
                            pass
                        params = {"pageNumber": 1, "pageSize": 25}
                        LOG.debug("Fetching inbox messages: %s params=%s", url, params)
                        try:
                            resp = requests.get(url, headers=headers, params=params,
                                                timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
                            LOG.debug("Inbox fetch status: %s", getattr(resp, 'status_code', None))
                            try:
                                payload = resp.json()
                            except Exception:
                                payload = None
                            rows = []
                            candidates = None
                            if isinstance(payload, list):
                                candidates = payload
                            elif isinstance(payload, dict):
                                for k in ('data', 'items', 'result', 'messages'):
                                    if isinstance(payload.get(k), list):
                                        candidates = payload.get(k)
                                        break
                                if (candidates is None and
                                        isinstance(payload.get('data'), dict) and
                                        isinstance(payload['data'].get('items'), list)):
                                    candidates = payload['data']['items']
                            if candidates is None:
                                LOG.debug("Inbox fetch returned unexpected payload: %s", type(payload))
                                candidates = []
                            for it in candidates:
                                if not isinstance(it, dict):
                                    continue
                                subj   = (it.get('subject') or it.get('title') or
                                          it.get('messageSubject') or '')
                                sender = (it.get('fromAddress') or it.get('from') or
                                          it.get('sender') or it.get('createdBy') or '')
                                time   = (it.get('createdAt') or it.get('sentAt') or
                                          it.get('time') or it.get('date') or '')
                                rows.append({'subject': subj, 'from': sender,
                                             'time': time, 'actions': ''})
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

    def _on_order_created(self, order: dict):
        try:
            LOG.info("OrdersWidget._on_order_created called: %s", order)
            model = getattr(self.orders_tab, 'table').model

            if isinstance(order, dict) and order.get('closed'):
                oid = order.get('id') or (order.get('payload') or {}).get('id')
                if oid is None:
                    LOG.warning("Close notification received without id: %s", order)
                    return
                removed = False
                try:
                    removed = model.remove_order_by_id(oid)
                except Exception:
                    LOG.exception("Failed removing closed order id=%s", oid)
                LOG.info("OrdersWidget %s closed order id=%s from model",
                         "removed" if removed else "did not find", oid)
                return

            norm = {
                'id':           order.get('id', 0),
                'time':         order.get('time') or order.get('createdAt') or '',
                'type':         order.get('type') or order.get('orderType') or '',
                'symbol':       order.get('symbol', ''),
                'lot':          order.get('lot') or order.get('lotSize') or order.get('volume') or 0,
                'entry_price':  order.get('entry_price') or order.get('entryPriceForPendingOrder') or 0,
                'entry_value':  order.get('entry_value', 0),
                'sl':           order.get('stopLoss', 0),
                'tp':           order.get('takeProfit', 0),
                'market_price': order.get('market_price', 0),
                'market_value': order.get('market_value', 0),
                'swap':         order.get('swap', 0),
                'commission':   order.get('commission', 0),
                'pl':           order.get('pl', 0),
                'pl_pct':       order.get('pl_pct', 0),
                'remarks':      order.get('remark', order.get('remarks', '')),
            }
            model.add_order(norm)
            LOG.info("OrdersWidget forwarded order to model: id=%s symbol=%s",
                     norm.get('id'), norm.get('symbol'))

            if self.order_updates_service is None:
                QTimer.singleShot(0, self._connect_order_updates)
        except Exception:
            LOG.exception("OrdersWidget failed to handle created order: %s", order)

    def _connect_price_updates(self):
        try:
            main = self.window()
            if not main:
                return
            lp = getattr(main, 'left_panel_widget', None)
            market = None
            if lp is not None and hasattr(lp, 'market_widget'):
                market = getattr(lp, 'market_widget')
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
        try:
            model = getattr(self.orders_tab, 'table').model
            model.update_market_price(symbol, sell, buy)
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
        try:
            account_id = account_info.get('account_id') or account_info.get('accountId')
            if not account_id:
                LOG.debug("OrdersWidget._on_account_changed_for_orders: No account ID")
                return
            if self.order_updates_service is not None:
                try:
                    self.order_updates_service.disconnect()
                    LOG.info("OrdersWidget: Disconnected previous OrderUpdatesService")
                except Exception:
                    LOG.exception("Error disconnecting previous OrderUpdatesService")
            LOG.info("OrdersWidget: Account changed to %s, initializing OrderUpdatesService", account_id)
            self._connect_order_updates(account_id)
        except Exception:
            LOG.exception("Error handling account change in OrdersWidget")

    def _on_account_id_changed(self, account_id: int):
        try:
            LOG.info("OrdersWidget._on_account_id_changed: account_id=%s", account_id)
            if self.order_updates_service is not None:
                try:
                    self.order_updates_service.disconnect()
                    LOG.debug("OrdersWidget: Disconnected previous OrderUpdatesService")
                except Exception:
                    LOG.exception("Error disconnecting previous OrderUpdatesService")
            self._connect_order_updates(account_id)
        except Exception:
            LOG.exception("Error handling account_id change in OrdersWidget")

    def _connect_order_updates(self, account_id=None):
        try:
            if (self.order_updates_service is not None and
                    self.order_updates_service.is_connected()):
                LOG.debug("OrderUpdatesService already connected, skipping re-initialization")
                return
            if not account_id:
                try:
                    store = AppStore()
                    current_account = store.get_current_account() or {}
                    account_id = (current_account.get('account_id') or
                                  current_account.get('accountId'))
                except Exception:
                    pass
            if not account_id:
                try:
                    if (hasattr(self, 'order_service') and self.order_service and
                            hasattr(self.order_service, '_last_account_id')):
                        account_id = self.order_service._last_account_id
                except Exception:
                    pass
            if not account_id:
                LOG.debug("OrdersWidget._connect_order_updates: No account ID available")
                return
            LOG.info("OrdersWidget._connect_order_updates: Starting for account %s", account_id)
            self.order_updates_service = OrderUpdatesService(account_id=account_id)
            model = getattr(self.orders_tab, 'table', None)
            if model is None:
                LOG.warning("OrdersWidget._connect_order_updates: Could not find orders table")
                return
            model = getattr(model, 'model', None)
            if model is None:
                LOG.warning("OrdersWidget._connect_order_updates: Could not find order model")
                return
            self.order_updates_service.orderUpdated.connect(
                lambda order_data: model.update_order_from_backend(order_data))
            self.order_updates_service.orderCreated.connect(
                lambda order_data: model.add_order(order_data))
            self.order_updates_service.orderClosed.connect(
                lambda order_id: model.remove_order_by_id(order_id))
            self.order_updates_service.connectionStatusChanged.connect(
                self._on_order_updates_connection_changed)
            LOG.debug("OrdersWidget connected OrderUpdatesService signals")
            self.order_updates_service.connect()
            LOG.info("OrdersWidget started OrderUpdatesService")
        except Exception:
            LOG.exception("Failed to initialize OrderUpdatesService")

    def _on_order_updates_connection_changed(self, is_connected):
        status = "CONNECTED" if is_connected else "DISCONNECTED"
        LOG.info("[OrderUpdatesService] Connection status changed: %s", status)


# Backwards compatibility alias
OrdersMainWindow = OrdersWidget