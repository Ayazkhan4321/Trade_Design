"""
Market Widget - Main widget with tabs, search, and symbol table
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QStackedWidget,
)
from PySide6.QtCore import Qt

from MarketWatch_jetfyx.ui.market_table import MarketTable
from MarketWatch_jetfyx.ui.symbol_tree_view import SymbolTreeView
from MarketWatch_jetfyx.components.tab_bar import TabBar
from MarketWatch_jetfyx.ui.search_dropdown import SearchDropdown
from MarketWatch_jetfyx.dialogs.settings_dialog import SettingsDialog
from MarketWatch_jetfyx.core.symbol_manager import SymbolManager
from MarketWatch_jetfyx.services.market_data_service import MarketDataService
from accounts.store import AppStore


class MarketWidget(QWidget):
    """Main market widget with tabbed interface for Favourites and All Symbols"""
    from PySide6.QtCore import Signal
    # Signal used to marshal hub updates into the GUI thread
    marketUpdate = Signal(object)

    # -------------------------
    # Qt lifecycle
    # -------------------------
    def closeEvent(self, event):
        """Cleanup SignalR connection when widget is closed."""
        if self.market_data_service:
            try:
                self.market_data_service.disconnect()
                print("[MarketWidget] SignalR connection disconnected on close.")
            except Exception as e:
                print(f"[MarketWidget] Error disconnecting SignalR: {e}")
        event.accept()

    # -------------------------
    # Init
    # -------------------------
    def __init__(
        self,
        settings_service=None,
        order_service=None,
        price_service=None,
        account_id=None,
    ):
        super().__init__()

        # Account
        self.account_id = account_id

        # Guards
        self._favorites_loading = False
        self._favorites_loaded = False

        # Symbol manager
        self.symbol_manager = SymbolManager(self)

        # Services
        self.settings_service = settings_service
        self.order_service = order_service

        if price_service is None:
            from MarketWatch_jetfyx.services.price_service import PriceService
            self.price_service = PriceService(symbol_manager=self.symbol_manager)
        else:
            self.price_service = price_service

        # App settings
        self.app_settings = (
            self.settings_service.get_settings()
            if self.settings_service
            else {
                "advance_view": False,
                "one_click_trade": False,
                "default_lot": 0.01,
                "default_lot_enabled": False,
            }
        )

        # Price updates: connect only once an account is set to avoid
        # receiving market updates before login/selection.

        # Subscribe to store account changes so MarketWidget reacts
        try:
            store = AppStore.instance()
            store.account_changed.connect(self.on_account_changed)
        except Exception:
            store = None

        # Market data (SignalR)
        self.market_data_service = None
        if self.account_id:
            self.market_data_service = MarketDataService(
                account_id=self.account_id,
                on_update_callback=self.marketUpdate.emit,
            )
            self.market_data_service.connect()

        # Track whether we've connected the priceUpdated signal to avoid
        # attempting to disconnect a signal that wasn't connected (PySide warnings).
        self._price_connected = False

        # UI state
        self.current_tab = 0
        self.favorites_table = None
        self.market_table = None
        self.all_symbols_tree = None

        # Build UI
        self._setup_ui()
        self._connect_signals()

        # Initial data load
        if self.account_id:
            self._fetch_and_load_symbols(self.account_id)

        if self.market_data_service:
            # Ensure incoming updates are marshalled to the GUI thread
            try:
                self.marketUpdate.connect(self._on_market_update)
            except Exception:
                pass
            try:
                self.market_data_service.set_on_update_callback(self.marketUpdate.emit)
            except Exception:
                pass

    # -------------------------
    # Market updates
    # -------------------------
    def _on_market_update(self, payload):
        if not isinstance(payload, dict):
            return

        symbol = payload.get("symbol")
        if not symbol:
            return

        is_new = self.symbol_manager.update_from_market_payload(payload)

        if is_new:
            self._update_tab_counts()
            if self.current_tab != 0:
                self._load_all_symbols()
        else:
            if self.current_tab == 0:
                self.favorites_table.update_symbols({symbol})
            else:
                self.all_symbols_tree.update_symbols({symbol})

    def _on_price_updated(self, symbol, sell, buy):
        if self.current_tab == 0:
            self.favorites_table.update_symbols({symbol})
        else:
            self.all_symbols_tree.update_symbols({symbol})

    def on_account_changed(self, account: dict):
        """Called when the application's active account changes.

        This forwards the account id to `set_account_id` to (re)start
        market data for the newly active account.
        """
        print(f"[MarketWidget] on_account_changed called with: {account}")
        if not account:
            return

        # Try several possible keys for account id
        account_id = account.get("account_id") or account.get("accountId") or account.get("id")
        if not account_id:
            return

        try:
            self.set_account_id(account_id)
        except Exception:
            pass

    # -------------------------
    # Backend symbol loading
    # -------------------------
    def _fetch_and_load_symbols(self, account_id):
        """Fetch favourite/watchlist symbols and load into SymbolManager"""
        import requests
        import jwt
        import logging
        logger = logging.getLogger(__name__)

        # Use centralized auth_service from `accounts` package
        from accounts.auth_service import get_token
        from MarketWatch_jetfyx.api.config import API_FAVOURITE_WATCHLIST_TEMPLATE, API_VERIFY_TLS, API_TIMEOUT

        token = get_token()
        logger.debug("[MarketWidget] Active account id: %s", self.account_id)

        if not token:
            logger.warning("[MarketWidget] No auth token available; cannot fetch favourite symbols")
            return

        try:
            accounts = jwt.decode(token, options={"verify_signature": False}).get("accounts")
            logger.debug("[MarketWidget] Token accounts: %s", accounts)
        except Exception:
            logger.debug("[MarketWidget] JWT decode failed (continuing)")

        url = API_FAVOURITE_WATCHLIST_TEMPLATE.format(accountId=account_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "JetFyXDesktop/1.0",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            logger.debug("[MarketWidget] Favourites fetch status: %s", resp.status_code)
            if resp.status_code == 200:
                data = resp.json()
                favorite_symbols = set()

                for symbol in data:
                    if "symbol" in symbol:
                        self.symbol_manager.update_from_market_payload(symbol)
                        favorite_symbols.add(symbol["symbol"])

                self.symbol_manager.set_favorites_silent(favorite_symbols)
                try:
                    self.symbol_manager.favoritesChanged.emit(list(favorite_symbols))
                except Exception:
                    logger.exception("Failed to emit favoritesChanged")
            else:
                logger.warning("[MarketWidget] Failed fetching favourites: %s %s", resp.status_code, getattr(resp, 'text', ''))
        except Exception:
            logger.exception("[MarketWidget] Failed loading symbols")

    # -------------------------
    # UI
    # -------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title label removed per user request (tab header already shows "Market View")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Symbols...")
        self.search.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
            """
        )

        self.tab_bar = TabBar()
        self._update_tab_counts()

        # Search dropdown (popup)
        self.search_dropdown = SearchDropdown(self.symbol_manager, parent=self)
        self.search_dropdown.hide()

        self.stacked_widget = QStackedWidget()

        self.favorites_table = MarketTable(
            self.symbol_manager,
            self.app_settings,
            self.order_service,
        )
        # Disable hover star in the favorites table (user requested)
        try:
            self.favorites_table.show_hover_favorite = False
        except Exception:
            pass
        # Disable hover background (only for favorites table)
        try:
            self.favorites_table.setStyleSheet(
                (self.favorites_table.styleSheet() or "")
                + "\nQTableView::item:hover { background: transparent; }"
            )
        except Exception:
            pass
        self.favorites_table.set_advance_view(
            self.app_settings.get("advance_view", False)
        )
        self.favorites_table.favoriteToggled.connect(
            self._on_favorite_toggled
        )

        self.all_symbols_tree = SymbolTreeView(
            self.symbol_manager,
            account_id=self.account_id,
            active_account_id=self.account_id,
        )
        self.all_symbols_tree.favoriteToggled.connect(
            self._on_favorite_toggled
        )

        self.stacked_widget.addWidget(self.favorites_table)
        self.stacked_widget.addWidget(self.all_symbols_tree)

        # title removed
        layout.addWidget(self.search)
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.stacked_widget)

    def set_account_id(self, account_id):
        """Set or change the active account for market data.

        This will (re)connect the MarketDataService for the given account
        and fetch the favourite/watchlist symbols for it.
        """
        if not account_id:
            return

        # If already set to this account, nothing to do
        if self.account_id == account_id and self.market_data_service:
            return

        self.account_id = account_id

        # Disconnect existing market data service if present
        if self.market_data_service:
            try:
                self.market_data_service.disconnect()
            except Exception:
                pass

        # Create and connect a new market data service for this account
        from MarketWatch_jetfyx.services.market_data_service import MarketDataService
        self.market_data_service = MarketDataService(
            account_id=self.account_id,
            on_update_callback=self._on_market_update,
        )
        try:
            self.market_data_service.connect()
        except Exception:
            pass

        # Fetch symbols for the new account
        try:
            self._fetch_and_load_symbols(self.account_id)
        except Exception:
            pass

        if self.market_data_service:
            self.market_data_service.set_on_update_callback(self._on_market_update)

        # Connect price update signal now that an account is active
        try:
            # Only disconnect if we previously connected — avoids PySide warnings
            if getattr(self, '_price_connected', False):
                try:
                    self.price_service.priceUpdated.disconnect(self._on_price_updated)
                except Exception:
                    pass
                self._price_connected = False

            # Connect once and remember that we did
            try:
                self.price_service.priceUpdated.connect(self._on_price_updated)
                self._price_connected = True
            except Exception:
                # Price service may not expose the signal in some tests/environments
                self._price_connected = False
        except Exception:
            pass

    # -------------------------
    # Signals
    # -------------------------
    def _connect_signals(self):
        self.search.textChanged.connect(self._on_search_changed)
        self.tab_bar.tabChanged.connect(self._on_tab_changed)
        self.tab_bar.settingsClicked.connect(self._on_settings_clicked)
        self.symbol_manager.favoritesChanged.connect(
            self._on_favorites_changed
        )

        # Search dropdown signals
        self.search_dropdown.symbolSelected.connect(self._on_search_symbol_selected)
        self.search_dropdown.favoriteToggled.connect(self._on_favorite_toggled)

        if self.settings_service:
            self.settings_service.settingsChanged.connect(
                self._on_settings_changed
            )

    # -------------------------
    # Tabs
    # -------------------------
    def _on_tab_changed(self, tab_index):
        if self.current_tab == 0:
            self.favorites_table.close_expanded_panel()
        else:
            self.all_symbols_tree.close_expanded_panel()

        self.current_tab = tab_index
        self.search.clear()
        self.stacked_widget.setCurrentIndex(tab_index)

        if tab_index == 1:
            self._load_all_symbols()

    def _load_all_symbols(self):
        all_symbols = self.symbol_manager.get_all_symbols()
        self.all_symbols_tree.set_symbols(all_symbols)

    def _position_search_dropdown(self):
        pos = self.search.mapToGlobal(self.search.rect().bottomLeft())
        self.search_dropdown.move(pos)
        self.search_dropdown.resize(self.search.width(), 250)

    # -------------------------
    # Search
    # -------------------------
    def _on_search_changed(self, text):
        # Show search dropdown with local results; do not mutate tables
        if not text.strip():
            self.search_dropdown.hide()
            return

        results = self.symbol_manager.search_symbols(text)
        self._position_search_dropdown()
        self.search_dropdown.show_results(results)
        # Ensure the search `QLineEdit` keeps focus so typing continues
        try:
            if not self.search.hasFocus():
                self.search.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass

    def _on_search_symbol_selected(self, symbol):
        # User selected a symbol from dropdown
        self.search.setText(symbol)
        self.search.setFocus()
        self.search_dropdown.hide()

    # -------------------------
    # Favorites
    # -------------------------
    def _on_favorite_toggled(self, symbol_name, is_favorite):
        from MarketWatch_jetfyx.services.favorite_service import (
            add_favorite,
            remove_favorite,
            get_favorites,
        )

        if self.account_id is not None:
            try:
                if is_favorite:
                    add_favorite(symbol_name, self.account_id)
                else:
                    favorites = get_favorites(self.account_id)
                    fav_id = next(
                        (
                            f.get("favouriteId")
                            or f.get("id")
                            or f.get("idFavorite")
                            for f in favorites
                            if f.get("symbol") == symbol_name
                        ),
                        None,
                    )
                    if fav_id:
                        remove_favorite(fav_id)
            except Exception as e:
                print("[MarketWidget] Favorite sync failed:", e)

        self._update_tab_counts()

    def _on_favorites_changed(self, favorites_list):
        self._update_tab_counts()
        self.favorites_table.set_symbols(
            self.symbol_manager.get_favorites()
        )
        # Refresh search dropdown visuals if visible
        try:
            if hasattr(self, 'search_dropdown') and self.search_dropdown.isVisible():
                current = self.search.text()
                if current.strip():
                    results = self.symbol_manager.search_symbols(current)
                    self.search_dropdown.show_results(results)
        except Exception:
            pass

    # -------------------------
    # Settings
    # -------------------------
    def _on_settings_clicked(self):
        dialog = SettingsDialog(self)
        dialog.set_settings(self.app_settings)

        if self.settings_service:
            dialog.settingsChanged.connect(
                self.settings_service.update
            )

        dialog.exec()

    def _on_settings_changed(self, settings):
        self.app_settings = settings
        self.favorites_table.app_settings = settings
        self.favorites_table.set_advance_view(
            settings.get("advance_view", False)
        )
        print("Settings updated:", settings)

    # -------------------------
    # Tabs count
    # -------------------------
    def _update_tab_counts(self):
        fav_count = self.symbol_manager.get_favorites_count()
        all_count = self.symbol_manager.get_symbols_count()
        self.tab_bar.update_counts(fav_count, all_count)

    def mousePressEvent(self, event):
        # Hide search dropdown when clicking outside search or dropdown
        try:
            if hasattr(self, 'search_dropdown') and self.search_dropdown.isVisible():
                gp = event.globalPos()
                inside_dropdown = self.search_dropdown.geometry().contains(self.search_dropdown.mapFromGlobal(gp))
                inside_search = self.search.geometry().contains(self.search.mapFromGlobal(gp))
                if not inside_dropdown and not inside_search:
                    self.search_dropdown.hide()
        except Exception:
            pass
        return super().mousePressEvent(event)
