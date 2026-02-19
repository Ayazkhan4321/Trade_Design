from PySide6.QtCore import QObject, Signal


class PriceService(QObject):
    priceUpdated = Signal(str, str, str)  # symbol, sell, buy

    def __init__(self, symbol_manager=None):
        super().__init__()
        self.price_cache = {}
        self.symbol_manager = symbol_manager

    def handle_market_update(self, payload):
        print(f"[PriceService] Received payload: {payload}")
        """
        Called by MarketDataService
        """
        symbol = payload.get("symbol")
        sell = payload.get("sell") or payload.get("ask")
        buy = payload.get("buy") or payload.get("bid")

        if not symbol or sell is None or buy is None:
            return

        self.update_price(symbol, str(sell), str(buy))

    def update_price(self, symbol, sell_price, buy_price):
        self.price_cache[symbol] = {
            "sell": sell_price,
            "buy": buy_price,
        }

        if self.symbol_manager:
            self.symbol_manager.update_from_market_payload({
                "symbol": symbol,
                "ask": sell_price,
                "bid": buy_price
                # Add more fields if available in payload
            })

        self.priceUpdated.emit(symbol, sell_price, buy_price)
