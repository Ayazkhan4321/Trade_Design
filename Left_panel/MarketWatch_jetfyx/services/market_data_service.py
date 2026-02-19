from signalrcore.hub_connection_builder import HubConnectionBuilder
from MarketWatch_jetfyx.api.config import HUB_BASE_URL
from accounts.auth_service import get_token
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    def set_on_update_callback(self, callback):
        """Set the callback to be called on market updates."""
        self.on_update_callback = callback

    def __init__(self, account_id, on_update_callback=None):
        # account_id is required to subscribe to market updates for a specific account.
        # The authorization token authenticates the user, but account_id tells the hub which account's data to send.
        self.account_id = account_id
        self.on_update_callback = on_update_callback
        self.connection = None
        # Running flag - helps drop updates during shutdown
        self._running = False

    def connect(self):
        token = get_token()
        masked = (token[:20] + "...") if token else None
        logger.debug("[MarketDataService] Retrieved token: %s", masked)

        if not token:
            logger.error("[MarketDataService] ERROR: No access token available. Cannot connect to SignalR hub.")
            return

        if not self.account_id:
            logger.error("[MarketDataService] ERROR: No account_id provided. Cannot subscribe to market updates.")
            return

        hub_url = f"{HUB_BASE_URL.rstrip('/')}/hubs/market"
        logger.info("[MarketDataService] Connecting to SignalR hub: %s", hub_url)

        # Use a dynamic factory so the SignalR client fetches the current token
        # at handshake time. Also avoid logging the full token.
        options = {
            "access_token_factory": lambda: get_token(),
            "headers": {
                "X-Client-App": "JetFyXDesktop",
                "User-Agent": "JetFyXDesktop/1.0",
            }
        }
        # Add Authorization header if we currently have a token
        if token:
            options["headers"]["Authorization"] = f"Bearer {token}"

        try:
            logger.debug("[MarketDataService] Building SignalR connection with options: %s", options)
            self.connection = (
                HubConnectionBuilder()
                .with_url(hub_url, options=options)
                .with_automatic_reconnect({
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                })
                .build()
            )

            # --- SignalR event listeners ---
            self.connection.on_open(lambda: logger.info("[MarketDataService] SignalR connection opened"))
            self.connection.on_close(lambda: logger.warning("[MarketDataService] SignalR connection closed"))
            self.connection.on_error(lambda e: logger.error("[MarketDataService] SignalR error: %s", e))
            self.connection.on(
                "ReceiveMarketUpdate",
                self._on_market_update
            )

            # Start connection
            logger.info("[MarketDataService] SignalR start called, waiting for connection...")
            self.connection.start()

            # Wait a short moment to ensure connection is open
            import time
            time.sleep(1)

            # mark as running only after connection has started
            self._running = True

            # Subscribe to account symbols
            logger.info("[MarketDataService] Subscribing to account %s", self.account_id)
            self.connection.send("SubscribeAccountSymbols", [self.account_id])
            logger.debug("[MarketDataService] Subscribed to account %s", self.account_id)

        except Exception:
            logger.exception("[MarketDataService] Failed to connect or subscribe")

    def _on_market_update(self, payload):
        logger.debug("[MarketDataService] Data received from hub: %s", payload)
        # Guard: drop updates if service is stopping/has stopped
        if not getattr(self, "_running", False):
            return
        import time
        now = time.time()
        logger.debug(f"[MarketDataService] Market update received: {payload}")
        # Handle both list and dict payloads
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    item = dict(item)  # copy to avoid mutating original
                    item['hub_received_timestamp'] = now
                    if self.on_update_callback:
                        try:
                            self.on_update_callback(item)
                        except Exception:
                            logger.exception("[MarketDataService] Error in on_update_callback")
        else:
            if isinstance(payload, dict):
                payload = dict(payload)
                payload['hub_received_timestamp'] = now
            if self.on_update_callback:
                try:
                    self.on_update_callback(payload)
                except Exception:
                    logger.exception("[MarketDataService] Error in on_update_callback")

    def disconnect(self):
        # Stop receiving updates and then stop the underlying connection.
        # Set _running False first so callbacks will early-return.
        try:
            self._running = False
        except Exception:
            pass

        if self.connection:
            try:
                self.connection.stop()
                logger.info("[MarketDataService] SignalR connection stopped")
            except Exception as e:
                logger.exception(f"[MarketDataService] Error stopping SignalR connection: {e}")
