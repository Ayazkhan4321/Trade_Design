"""
Symbol Manager
Manages all trading symbols, live updates, and favorites
"""

from PySide6.QtCore import QObject, Signal
import time
import logging

logger = logging.getLogger("SymbolManager")
# Do not force a level here; let the application configure logging centrally.


class SymbolManager(QObject):
    """
    Central store for all symbols and their state
    """

    symbolsUpdated = Signal()
    favoritesChanged = Signal(list)
    priceUpdated = Signal(str, str, str)  # symbol, sell, buy

    def __init__(self, parent=None):
        super().__init__(parent)

        self._symbols = {}
        self._favorites = set()

        # ⏱ Throttle UI spam (prevents SignalR collapse)
        self._last_emit_ts = 0
        self._emit_interval = 0.1  # seconds

    # --------------------------------------------------
    # 📊 BASIC INFO
    # --------------------------------------------------

    def get_symbols_count(self):
        return len(self._symbols)

    def get_all_symbols(self):
        return list(self._symbols.values())

    # --------------------------------------------------
    # 🔄 LIVE MARKET UPDATE (FROM SIGNALR)
    # --------------------------------------------------

    def update_from_market_payload(self, payload: dict) -> bool:
        """
        Called from SignalR ReceiveMarketUpdate
        Returns True if symbol is new
        """

        if not isinstance(payload, dict):
            logger.warning("Invalid payload type: %s", type(payload))
            return False

        logger.debug("📩 Market payload received: %s", payload)

        symbol = payload.get("symbol")
        if not symbol:
            logger.warning("Payload without symbol: %s", payload)
            return False

        is_new = symbol not in self._symbols

        data = self._symbols.get(symbol, {
            "symbol": symbol,
            "sell": "",
            "buy": "",
            "mid": "",
            "low": "",
            "high": "",
            "time": "",
            "spread": "",
            "change": None,
            "isPositive": None,
            "_raw_bid": None,
            "_raw_ask": None,
            "_raw_mid": None,
        })

        old_sell = data["sell"]
        old_buy = data["buy"]

        # ---- Raw values ----
        bid = payload.get("bid")
        ask = payload.get("ask")

        # ---- String values (for UI) ----
        if ask is not None:
            data["sell"] = f"{ask:.5f}"
        if bid is not None:
            data["buy"] = f"{bid:.5f}"

        data["low"] = str(payload.get("low", data["low"]))
        data["high"] = str(payload.get("high", data["high"]))
        # Propagate hub_received_timestamp for latency logging
        if "hub_received_timestamp" in payload:
            data["hub_received_timestamp"] = payload["hub_received_timestamp"]
        # print(f"[DEBUG][SymbolManager] Incoming payload for {symbol}: {payload}")
        data["time"] = payload.get("timestamp", payload.get("ts", data["time"]))
        # print(f"[DEBUG][SymbolManager] After update, data['time'] for {symbol}: {data['time']}")

        # 🔔 Emit priceUpdated only if price actually changed
        if data["sell"] != old_sell or data["buy"] != old_buy:
            logger.debug("💰 Price updated for %s | sell=%s buy=%s",
                         symbol, data["sell"], data["buy"])
            try:
                self.priceUpdated.emit(symbol, data["sell"], data["buy"])
            except RuntimeError as e:
                logger.warning("Price update emit failed (possibly deleted): %s", e)
            except Exception:
                logger.exception("Unexpected error emitting priceUpdated")

        # ---- Mid / change / spread ----
        if bid is not None and ask is not None:
            mid = (bid + ask) / 2
            prev = data["_raw_mid"]

            data["_raw_bid"] = bid
            data["_raw_ask"] = ask
            data["_raw_mid"] = mid
            data["mid"] = f"{mid:.5f}"
            data["spread"] = f"{abs(ask - bid):.5f}"

            if prev is not None:
                delta = mid - prev
                data["change"] = round(delta, 5)
                data["isPositive"] = delta >= 0

        self._symbols[symbol] = data

        # 🧯 Throttle massive UI refresh spam
        now = time.time()
        if now - self._last_emit_ts >= self._emit_interval:
            self._last_emit_ts = now
            try:
                self.symbolsUpdated.emit()
            except RuntimeError as e:
                logger.warning("Symbols updated emit failed (possibly deleted): %s", e)
            except Exception:
                logger.exception("Unexpected error emitting symbolsUpdated")

        return is_new

    # --------------------------------------------------
    # ⭐ FAVORITES (NO NETWORK CALLS HERE)
    # --------------------------------------------------

    def set_favorites_silent(self, symbols: set):
        """
        Used on startup ONLY.
        Must never trigger API calls.
        """
        self._favorites = set(symbols)

    def toggle_favorite(self, symbol: str):
        if symbol in self._favorites:
            self._favorites.remove(symbol)
        else:
            self._favorites.add(symbol)

        logger.debug("⭐ Favorites changed: %s", self._favorites)
        self.favoritesChanged.emit(list(self._favorites))

    def add_favorite(self, symbol: str):
        if symbol not in self._favorites:
            self._favorites.add(symbol)
            self.favoritesChanged.emit(list(self._favorites))

    def remove_favorite(self, symbol: str):
        if symbol in self._favorites:
            self._favorites.remove(symbol)
            self.favoritesChanged.emit(list(self._favorites))

    def is_favorite(self, symbol: str) -> bool:
        return symbol in self._favorites

    def get_favorites(self):
        """
        IMPORTANT:
        This must NOT call any API.
        Only returns local cached data.
        """
        return [
            self._symbols[s]
            for s in self._favorites
            if s in self._symbols
        ]

    def get_favorites_count(self):
        return len(self._favorites)

    def reset(self):
        """
        Reset all symbol state. Keeps the QObject identity intact so
        connected slots/signals remain valid. Use this on account switch
        instead of recreating the SymbolManager.
        """
        logger.debug("SymbolManager.reset() called - clearing symbols and favorites")
        self._symbols = {}
        self._favorites = set()
        try:
            self.favoritesChanged.emit(list(self._favorites))
        except Exception:
            logger.exception("Failed to emit favoritesChanged during reset")
        try:
            self.symbolsUpdated.emit()
        except Exception:
            logger.exception("Failed to emit symbolsUpdated during reset")

    # --------------------------------------------------
    # 🔍 SEARCH (LOCAL ONLY)
    # --------------------------------------------------

    def search_symbols(self, query: str):
        q = query.lower().strip()
        return [
            s for s in self._symbols.values()
            if q in s["symbol"].lower()
        ]
