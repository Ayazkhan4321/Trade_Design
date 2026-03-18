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
from plugins.tradingview_plugin import TradingChartPlugin
try:
    from Theme.theme_manager import ThemeManager as _ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _ThemeManager = None
    _THEME_AVAILABLE = False


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
        self.chart_plugin = TradingChartPlugin()

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

        # Connect theme manager
        if _THEME_AVAILABLE:
            try:
                _ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

        if self.market_data_service:
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
                if self.favorites_table and hasattr(self.favorites_table, 'update_symbols'):
                    try:
                        self.favorites_table.update_symbols({symbol})
                    except RuntimeError:
                        pass
            else:
                if self.all_symbols_tree and hasattr(self.all_symbols_tree, 'update_symbols'):
                    try:
                        self.all_symbols_tree.update_symbols({symbol})
                    except RuntimeError:
                        pass

    def _on_price_updated(self, symbol, sell, buy):
        if self.current_tab == 0:
            if self.favorites_table and hasattr(self.favorites_table, 'update_symbols'):
                try:
                    self.favorites_table.update_symbols({symbol})
                except RuntimeError:
                    pass
        else:
            if self.all_symbols_tree and hasattr(self.all_symbols_tree, 'update_symbols'):
                try:
                    self.all_symbols_tree.update_symbols({symbol})
                except RuntimeError:
                    pass

    def on_account_changed(self, account: dict):
        """Called when the application's active account changes."""
        print(f"[MarketWidget] on_account_changed called with: {account}")
        if not account:
            return

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

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Symbols...")
        self.search.setObjectName("MarketSearch")

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
        self.favorites_table.symbolSelected.connect(self._on_symbol_selected)
        # show_hover_favorite = True so the ★ appears on hover in the favourites tab
        try:
            self.favorites_table.show_hover_favorite = True
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

        layout.addWidget(self.search)
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.stacked_widget)

        # Apply initial theme styles
        self.apply_theme()

    def set_account_id(self, account_id):
        """Set or change the active account for market data."""
        if not account_id:
            return

        if self.account_id == account_id and self.market_data_service:
            return

        self.account_id = account_id

        if self.market_data_service:
            try:
                self.market_data_service.disconnect()
            except Exception:
                pass

        from MarketWatch_jetfyx.services.market_data_service import MarketDataService
        self.market_data_service = MarketDataService(
            account_id=self.account_id,
            on_update_callback=self._on_market_update,
        )
        try:
            self.market_data_service.connect()
        except Exception:
            pass

        try:
            self._fetch_and_load_symbols(self.account_id)
        except Exception:
            pass

        if self.market_data_service:
            self.market_data_service.set_on_update_callback(self._on_market_update)

        try:
            if getattr(self, '_price_connected', False):
                try:
                    self.price_service.priceUpdated.disconnect(self._on_price_updated)
                except Exception:
                    pass
                self._price_connected = False

            try:
                self.price_service.priceUpdated.connect(self._on_price_updated)
                self._price_connected = True
            except Exception:
                self._price_connected = False
        except Exception:
            pass

    # -------------------------
    # Theme
    # -------------------------
    def _get_tokens(self) -> dict:
        """Return current theme tokens, or empty dict if theme unavailable."""
        if _THEME_AVAILABLE:
            try:
                return _ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    def apply_theme(self):
        """Re-style all child widgets using current theme tokens."""
        t = self._get_tokens()

        bg_input   = t.get("bg_input",       "#f5f7fa")
        text_p     = t.get("text_primary",   "#1a202c")
        border_p   = t.get("border_primary", "#e5e7eb")
        border_foc = t.get("border_focus",   "#1976d2")
        bg_panel   = t.get("bg_panel",       "#ffffff")
        bg_sel     = t.get("bg_selected",    "#1565c0")
        text_sel   = t.get("text_selected",  "#ffffff")
        text_hdr   = t.get("text_secondary", "#4a5568")
        border_gr  = t.get("border_separator","#e5e7eb")
        bg_alt     = t.get("bg_row_alt",     "#f9fafb")
        bg_widget  = t.get("bg_widget",      "#ffffff")
        accent     = t.get("accent",         "#1976d2")
        is_dark    = t.get("is_dark", "false") in ("true", "1", "True")

        # Compute hover color from accent — works for any theme colour
        # Priority: explicit bg_row_hover token → derived from accent → fallback
        _raw_hover = t.get("bg_row_hover", "")
        if _raw_hover and _raw_hover not in ("transparent", ""):
            bg_hover = _raw_hover
        else:
            # Blend: 85% panel + 15% accent
            try:
                from PySide6.QtGui import QColor as _QC
                _ac   = _QC(accent)
                _base = _QC(bg_panel)
                _r = int(_base.red()   * 0.92 + _ac.red()   * 0.08)
                _g = int(_base.green() * 0.92 + _ac.green() * 0.08)
                _b = int(_base.blue()  * 0.92 + _ac.blue()  * 0.08)
                bg_hover = _QC(_r, _g, _b).name()
            except Exception:
                bg_hover = "#1e2d3d" if is_dark else "#e8f5e9"

        # ── Search field ──────────────────────────────────────────────
        if hasattr(self, "search"):
            self.search.setStyleSheet(f"""
                QLineEdit {{
                    padding: 8px;
                    background: {bg_input};
                    color: {text_p};
                    border: 1px solid {border_p};
                    border-radius: 4px;
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {border_foc};
                }}
            """)

        # ── Favourites table ─────────────────────────────────────────
        if hasattr(self, "favorites_table") and self.favorites_table:
            self.favorites_table.setStyleSheet(f"""
                QTableView {{
                    background: {bg_panel};
                    alternate-background-color: {bg_alt};
                    color: {text_p};
                    border: none;
                    gridline-color: {border_gr};
                }}
                QTableView::item:selected {{
                    background: {bg_sel};
                    color: {text_sel};
                }}
                /* hover background handled by RowHoverDelegate / AdvanceViewDelegate */
                QHeaderView::section {{
                    background: {bg_panel};
                    color: {text_hdr};
                    border: none;
                    border-bottom: 1px solid {border_p};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 8px;
                }}
            """)
            # Push computed hover color directly to delegates — bypasses all token lookup
            try:
                ft = self.favorites_table
                if hasattr(ft, 'normal_delegate'):
                    ft.normal_delegate.hover_color = bg_hover
                if hasattr(ft, 'advance_delegate'):
                    ft.advance_delegate.hover_color = bg_hover
            except Exception:
                pass
            try:
                self.favorites_table.viewport().update()
            except Exception:
                pass

        # ── All symbols tree ─────────────────────────────────────────
        if hasattr(self, "all_symbols_tree") and self.all_symbols_tree:
            if hasattr(self.all_symbols_tree, "apply_theme"):
                try:
                    self.all_symbols_tree.apply_theme()
                except Exception:
                    pass

        # ── Tab bar ───────────────────────────────────────────────────
        if hasattr(self, "tab_bar") and self.tab_bar:
            if hasattr(self.tab_bar, "apply_theme"):
                try:
                    self.tab_bar.apply_theme()
                except Exception:
                    pass

    # -------------------------
    def _connect_signals(self):
        self.search.textChanged.connect(self._on_search_changed)
        self.tab_bar.tabChanged.connect(self._on_tab_changed)
        self.tab_bar.settingsClicked.connect(self._on_settings_clicked)
        self.symbol_manager.favoritesChanged.connect(
            self._on_favorites_changed
        )
        self.search_dropdown.symbolSelected.connect(self._on_search_symbol_selected)
        self.search_dropdown.favoriteToggled.connect(self._on_favorite_toggled)

        # ← ADDED: wire all-symbols tree so clicking there also loads chart
        if hasattr(self.all_symbols_tree, 'symbolSelected'):
            self.all_symbols_tree.symbolSelected.connect(self._on_symbol_selected)

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
        if not text.strip():
            self.search_dropdown.hide()
            return

        results = self.symbol_manager.search_symbols(text)
        self._position_search_dropdown()
        self.search_dropdown.show_results(results)
        try:
            if not self.search.hasFocus():
                self.search.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass

    def _on_search_symbol_selected(self, symbol):
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
    
    def _on_symbol_selected(self, symbol: str):
        """Called when user clicks a symbol in the table"""
    
        print("Selected symbol:", symbol)
    
        # Request candle data
        if hasattr(self, "chart_plugin"):
            self.chart_plugin.load_symbol(symbol)

    def _on_favorites_changed(self, favorites_list):
        self._update_tab_counts()
        self.favorites_table.set_symbols(
            self.symbol_manager.get_favorites()
        )
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

        # SettingsDialog subscribes to ThemeManager.theme_changed internally
        # and applies all tokens itself — no external stylesheet injection needed.

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