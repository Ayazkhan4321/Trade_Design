"""
OrderUpdatesService - WebSocket/SignalR connection for real-time order updates.

Receives real-time P&L, price, swap, and other order updates from the backend
via SignalR Hub at /hubs/orders. The service emits signals when order data changes.
"""

from PySide6.QtCore import QObject, Signal
from signalrcore.hub_connection_builder import HubConnectionBuilder
from api.config import HUB_ORDERS
from accounts.auth_service import get_token
import logging

LOG = logging.getLogger(__name__)


class OrderUpdatesService(QObject):
    """
    Service for receiving real-time order updates via SignalR.
    
    Signals:
        orderUpdated: Emitted when an order's data changes (price, P&L, etc.)
                     Payload: dict with order_id, symbol, market_price, pl, pl_pct, etc.
        orderCreated: Emitted when a new order is created
        orderClosed: Emitted when an order is closed/deleted
        connectionStatusChanged: Emitted when connection status changes (connected/disconnected)
    """
    
    orderUpdated = Signal(dict)
    orderCreated = Signal(dict)
    orderClosed = Signal(int)  # order_id
    connectionStatusChanged = Signal(bool)  # True = connected, False = disconnected
    
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id
        self.connection = None
        self._running = False
        self._connected = False
    
    def connect(self):
        """Establish WebSocket connection to orders hub."""
        token = get_token()
        if not token:
            LOG.error("[OrderUpdatesService] No access token available")
            return
        
        if not self.account_id:
            LOG.error("[OrderUpdatesService] No account_id provided")
            return
        
        LOG.info("[OrderUpdatesService] Connecting to orders hub for account %s", self.account_id)
        
        try:
            options = {
                "access_token_factory": lambda: get_token(),
                "headers": {
                    "X-Client-App": "JetFyXDesktop",
                    "User-Agent": "JetFyXDesktop/1.0",
                }
            }
            if token:
                options["headers"]["Authorization"] = f"Bearer {token}"
            
            self.connection = (
                HubConnectionBuilder()
                .with_url(HUB_ORDERS, options=options)
                .with_automatic_reconnect({
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                })
                .build()
            )
            
            # Event listeners
            self.connection.on_open(self._on_open)
            self.connection.on_close(self._on_close)
            self.connection.on_error(self._on_error)
            
            # Real-time order update handlers
            self.connection.on("ReceiveOrderUpdate", self._on_order_update)
            self.connection.on("ReceiveOrderCreated", self._on_order_created)
            self.connection.on("ReceiveOrderClosed", self._on_order_closed)
            
            # Start connection
            LOG.info("[OrderUpdatesService] Starting SignalR connection...")
            self.connection.start()
            
            # Wait for connection to establish
            import time
            time.sleep(1)
            
            self._running = True
            
            # Subscribe to account orders
            LOG.info("[OrderUpdatesService] Subscribing to orders for account %s", self.account_id)
            try:
                # Use send() with list of arguments
                self.connection.send("SubscribeToAccount", [self.account_id])
                LOG.debug("[OrderUpdatesService] Successfully subscribed to account %s", self.account_id)
            except Exception:
                LOG.exception("[OrderUpdatesService] Failed to subscribe to account")
            
        except Exception:
            LOG.exception("[OrderUpdatesService] Failed to connect")
            self.connectionStatusChanged.emit(False)
    
    def _on_open(self):
        """Called when connection opens."""
        LOG.info("[OrderUpdatesService] Connected to orders hub")
        self._connected = True
        
        # Re-subscribe to account on reconnect
        if self._running and self.account_id:
            try:
                LOG.debug("[OrderUpdatesService] Re-subscribing to account %s after reconnect", self.account_id)
                self.connection.send("SubscribeToAccount", [self.account_id])
            except Exception:
                LOG.exception("[OrderUpdatesService] Failed to re-subscribe after reconnect")
        
        self.connectionStatusChanged.emit(True)
    
    def _on_close(self):
        """Called when connection closes."""
        LOG.warning("[OrderUpdatesService] Disconnected from orders hub")
        self._connected = False
        self.connectionStatusChanged.emit(False)
    
    def _on_error(self, error):
        """Called when connection error occurs."""
        LOG.error("[OrderUpdatesService] Connection error: %s", error)
        self._connected = False
        self.connectionStatusChanged.emit(False)
    
    def _on_order_update(self, payload):
        """
        Handles real-time order updates from backend.
        
        Payload structure expected (can be nested):
        - dict: {'id': 28678, 'symbol': 'NZDUSD', 'market_price': 0.70071, ...}
        - list[dict]: [{'id': 28678, ...}, {'id': 28679, ...}]
        - list[list[dict]]: [[{'id': 28678, ...}]] (nested, needs unwrapping)
        """
        if not self._running or not payload:
            return
        
        # Unwrap nested lists
        if isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], list):
            # Nested list - unwrap it
            LOG.debug("[OrderUpdatesService] Order update received nested list: unwrapping list[list]")
            for nested_item in payload:
                if isinstance(nested_item, list):
                    for item in nested_item:
                        if isinstance(item, dict):
                            self._process_order_update(item)
                elif isinstance(nested_item, dict):
                    self._process_order_update(nested_item)
        # Handle normal list or dict payloads
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    self._process_order_update(item)
        elif isinstance(payload, dict):
            self._process_order_update(payload)
    
    def _process_order_update(self, order_data):
        """Process a single order update."""
        try:
            order_id = order_data.get('id') or order_data.get('orderId')
            
            # Map backend field names (camelCase) to internal names (snake_case)
            if 'marketPrice' in order_data:
                order_data['market_price'] = float(order_data['marketPrice'])
            if 'marketValue' in order_data:
                order_data['market_value'] = float(order_data['marketValue'])
            else:
                order_data['market_value'] = 0.0
            
            if 'profitOrLoss' in order_data:
                order_data['pl'] = float(order_data['profitOrLoss'])
            if 'profitOrLossInPercentage' in order_data:
                order_data['pl_pct'] = float(order_data['profitOrLossInPercentage'])
            
            if 'swap' in order_data:
                order_data['swap'] = float(order_data['swap'])
            if 'commission' in order_data:
                order_data['commission'] = float(order_data['commission'])
            
            LOG.info("[OrderUpdatesService] Processing order update: id=%s, symbol=%s, market_price=%.2f, pl=%.2f, pl_pct=%.2f",
                      order_id, order_data.get('symbol'), order_data.get('market_price', 0), 
                      order_data.get('pl', 0), order_data.get('pl_pct', 0))
            
            self.orderUpdated.emit(order_data)
        except Exception:
            LOG.exception("[OrderUpdatesService] Error processing order update")
    
    def _on_order_created(self, payload):
        """Handles when a new order is created."""
        if not self._running or not payload:
            return
        
        LOG.info("[OrderUpdatesService] Order created: %s", 
                payload.get('id') if isinstance(payload, dict) else payload)
        
        if isinstance(payload, dict):
            self.orderCreated.emit(payload)
    
    def _on_order_closed(self, payload):
        """Handles when an order is closed/deleted."""
        if not self._running or not payload:
            return
        
        try:
            order_id = int(payload) if isinstance(payload, (int, str)) else payload.get('id')
            LOG.info("[OrderUpdatesService] Order closed: %s", order_id)
            self.orderClosed.emit(order_id)
        except Exception:
            LOG.exception("[OrderUpdatesService] Error processing order closed")
    
    def disconnect(self):
        """Stop receiving updates and close connection."""
        LOG.info("[OrderUpdatesService] Disconnecting...")
        self._running = False
        
        if self.connection:
            try:
                self.connection.stop()
                LOG.info("[OrderUpdatesService] Disconnected")
            except Exception:
                LOG.exception("[OrderUpdatesService] Error stopping connection")
        
        self._connected = False
        self.connectionStatusChanged.emit(False)
    
    def is_connected(self):
        """Check if currently connected."""
        return self._connected
