"""Order Service - handles placing orders via API and notifying listeners."""

from . import __name__ as _svc
import logging
from typing import Callable
import time

import requests
from api.config import API_BASE_URL, API_TIMEOUT, API_VERIFY_TLS, API_ORDERS, API_ORDERS_CLOSE
from api.config import API_ORDERS_HISTORY
from auth.session import get_token

# Try to access the app-wide account store to infer current account when not provided
try:
    from accounts.store import AppStore as CanonicalAppStore
except Exception:
    CanonicalAppStore = None


LOG = logging.getLogger(__name__)


class OrderService:
    def __init__(self):
        self.active_orders = []
        self.order_history = []
        self._listeners = []
        self._last_account_id = None  # Track the last account ID used for fetching

    def register_listener(self, callback: Callable[[dict], None]):
        """Register a callback that's called with the created order dict."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self, order: dict):
        for cb in list(self._listeners):
            try:
                cb(order)
            except Exception:
                LOG.exception("Order listener raised")

    def place_market_order(self, symbol, order_type, volume, stop_loss=None, take_profit=None, remarks="", account_id=0):
        """Place a market order via the backend API and notify listeners.

        Returns the created order dict on success, or None on failure.
        """
        # Build payload for immediate market orders (do NOT include pending-only fields)
        payload = {
            "symbol": symbol,
            "orderType": order_type,
            "lotSize": float(volume),
            "stopLoss": stop_loss or 0,
            "takeProfit": take_profit or 0,
            "remark": remarks or "",
            "status": "Ongoing",
            "accountId": int(account_id or 0),
        }

        # Ensure accountId is set: prefer explicit param, else try app store
        if not account_id:
            try:
                if CanonicalAppStore:
                    cur = CanonicalAppStore.instance().get_current_account()
                    account_id = cur.get('account_id') or cur.get('accountId') or cur.get('id') or 0
            except Exception:
                account_id = 0

        payload["accountId"] = int(account_id or 0)

        url = API_ORDERS
        LOG.info("Placing order: url=%s account=%s type=%s symbol=%s lot=%s", url, account_id, order_type, symbol, volume)
        LOG.debug("Order payload: %s", payload)
        # Prepare headers with auth token and referer/origin to satisfy server checks
        headers = {}
        try:
            token = get_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        except Exception:
            LOG.debug("No auth token available when placing order")
        # Some backends validate Origin/Referer for non-browser clients; include Referer
        headers.setdefault('Referer', API_BASE_URL)
        resp = None
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            LOG.info("Order POST response: status=%s", resp.status_code)
            try:
                data = resp.json()
                LOG.debug("Order POST response json: %s", data)
            except Exception:
                LOG.debug("Order POST response text: %s", getattr(resp, 'text', '<no-text>'))
                data = {}

            resp.raise_for_status()

            # Normalize backend response into the table-friendly dict
            # Determine sensible entry/market prices from response (be permissive)
            entry_price = (
                data.get("entryPrice") or data.get("executedPrice") or
                data.get("entryPriceForPendingOrder") or data.get("marketPrice") or 0
            )
            market_price = data.get("marketPrice") or entry_price or 0

            try:
                entry_price = float(entry_price)
            except Exception:
                entry_price = 0.0
            try:
                market_price = float(market_price)
            except Exception:
                market_price = 0.0

            order = {
                "id": data.get("id") or data.get("orderId") or 0,
                "time": data.get("createdAt") or time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": order_type,
                "symbol": symbol,
                "lot": float(volume),
                "entry_price": entry_price,
                "entry_value": float(entry_price) * float(volume) if entry_price and volume else 0.0,
                "sl": payload["stopLoss"],
                "tp": payload["takeProfit"],
                "market_price": market_price,
                "market_value": float(market_price) * float(volume) if market_price and volume else 0.0,
                "swap": 0.0,
                "commission": 0.0,
                "pl": 0.0,
                "pl_pct": 0.0,
                "remarks": payload.get("remark", ""),
            }

            self.active_orders.append(order)
            LOG.info("Order placed and appended locally: id=%s symbol=%s", order.get('id'), order.get('symbol'))
            self._notify_listeners(order)
            return order
        except Exception:
            if resp is not None:
                LOG.error("Order POST failed: status=%s text=%s", getattr(resp, 'status_code', None), getattr(resp, 'text', None))
            LOG.exception("Failed placing order to %s", url)
            return None

    def place_limit_order(self, *args, **kwargs):
        # For now, forward to place_market_order or implement as needed
        return self.place_market_order(*args, **kwargs)

    def get_active_orders(self):
        return list(self.active_orders)

    def fetch_orders(self, account_id: int = 0, page_number: int = 1, page_size: int = 1000):
        """Fetch existing orders from the backend for given account and store locally.

        Returns the list of normalized orders or empty list on failure.
        """
        url = API_ORDERS
        # Ensure accountId fallback similar to place_market_order
        if not account_id:
            try:
                if CanonicalAppStore:
                    cur = CanonicalAppStore.instance().get_current_account()
                    account_id = cur.get('account_id') or cur.get('accountId') or cur.get('id') or 0
            except Exception:
                account_id = 0

        params = {
            'AccountId': int(account_id or 0),
            'TabMode': 'Order',
            'PageNumber': int(page_number),
            'PageSize': int(page_size),
        }

        headers = {}
        try:
            token = get_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        except Exception:
            LOG.debug("No auth token available when fetching orders")
        headers.setdefault('Referer', API_BASE_URL)

        try:
            LOG.info("Fetching orders: url=%s params=%s", url, params)
            resp = requests.get(url, params=params, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            LOG.info("Orders GET response: status=%s", getattr(resp, 'status_code', None))
            try:
                data = resp.json()
            except Exception:
                LOG.debug("Orders GET response text: %s", getattr(resp, 'text', None))
                data = []

            if not isinstance(data, list):
                # Some backends wrap the actual results under a top-level `data` key
                # (or another wrapper). Try the expected `data` first, then fall
                # back to searching common wrapper keys.
                wrapper_keys = ['items', 'results', 'orders', 'value', 'payload']
                extracted = None
                if isinstance(data, dict):
                    LOG.info("Orders GET returned dict top-level keys: %s", list(data.keys()))

                    # Prefer explicit `data` wrapper when present
                    if 'data' in data:
                        payload = data.get('data')
                        if isinstance(payload, list):
                            extracted = payload
                            LOG.info("Found orders list under top-level 'data' key")
                        elif isinstance(payload, dict):
                            # Search common list keys inside the `data` object
                            for k in wrapper_keys:
                                v = payload.get(k)
                                if isinstance(v, list):
                                    extracted = v
                                    LOG.info("Found orders list under data['%s']", k)
                                    break

                    # If still nothing, look for lists directly at top-level
                    if extracted is None:
                        for k in wrapper_keys + list(data.keys()):
                            v = data.get(k)
                            if isinstance(v, list):
                                extracted = v
                                LOG.info("Found orders list under key '%s'", k)
                                break

                if isinstance(extracted, list):
                    data = extracted
                else:
                    LOG.warning("Unexpected orders payload shape (no list found). Top-level keys: %s", type(data))
                    data = []

            normalized = []
            for item in data:
                try:
                    entry_price = (
                        item.get('entryPrice') or item.get('executedPrice') or
                        item.get('entryPriceForPendingOrder') or item.get('marketPrice') or 0
                    )
                    market_price = item.get('marketPrice') or entry_price or 0
                    try:
                        entry_price = float(entry_price)
                    except Exception:
                        entry_price = 0.0
                    try:
                        market_price = float(market_price)
                    except Exception:
                        market_price = 0.0

                    lot = float(item.get('lot') or item.get('lotSize') or item.get('volume') or 0)

                    order = {
                        'id': item.get('id') or item.get('orderId') or 0,
                        'time': item.get('createdAt') or item.get('time') or '',
                        'type': item.get('orderType') or item.get('type') or '',
                        'symbol': item.get('symbol') or '',
                        'lot': lot,
                        'entry_price': entry_price,
                        'entry_value': float(entry_price) * lot if entry_price and lot else 0.0,
                        'sl': item.get('stopLoss', 0),
                        'tp': item.get('takeProfit', 0),
                        'market_price': market_price,
                        'market_value': float(market_price) * lot if market_price and lot else 0.0,
                        'swap': item.get('swap', 0.0),
                        'commission': item.get('commission', 0.0),
                        'pl': 0.0,
                        'pl_pct': 0.0,
                        'remarks': item.get('remark') or item.get('remarks') or '',
                    }
                    normalized.append(order)
                except Exception:
                    LOG.exception("Failed to normalize order item: %s", item)

            # Replace local cache and return
            self.active_orders = list(normalized)
            # Store account_id for fallback use in _connect_order_updates()
            if account_id:
                self._last_account_id = int(account_id)
                LOG.debug("Stored _last_account_id=%s for fallback account resolution", self._last_account_id)
            LOG.info("Fetched %s orders for account %s", len(self.active_orders), account_id)
            return list(self.active_orders)
        except Exception:
            LOG.exception("Failed fetching orders from %s", url)
            return []

    def cancel_order(self, order_id):
        """Close/cancel an order by sending a close payload to the API.

        Some backends require updating the order resource with a status
        payload (e.g. {"id": <id>, "status": 1}) to close an executed
        order. This method sends that payload (PUT) and updates the local
        cache from the response when available.
        """
        if not order_id:
            LOG.warning("cancel_order called without order_id")
            return False

        # Safely parse ID to ensure the backend receives the exact type it expects
        try:
            oid = int(float(order_id))
        except Exception:
            oid = order_id

        url = API_ORDERS_CLOSE.format(orderId=oid)
        payload = { 'id': oid, 'status': 1 }

        headers = {}
        try:
            token = get_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        except Exception:
            LOG.debug("No auth token available when cancelling/closing order")
        headers.setdefault('Referer', API_BASE_URL)

        try:
            LOG.info("Closing order %s via %s payload=%s", oid, url, payload)
            resp = requests.put(url, json=payload, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            LOG.info("Order close response: status=%s", getattr(resp, 'status_code', None))
            
            if resp is None:
                LOG.error("No response when attempting to close order %s", oid)
                return False

            # Accept ALL 2xx success codes (200, 201, 202, 204)
            if not (200 <= resp.status_code < 300):
                LOG.error("Failed to close order %s: status=%s text=%s", oid, getattr(resp, 'status_code', None), getattr(resp, 'text', None))
                return False

            try:
                data = resp.json()
            except Exception:
                data = None

            item = None
            if isinstance(data, dict):
                # API returns { message, statusCode, data: { ... } }
                item = data.get('data') or data

            # Update local cache if server returned the closed order
            if isinstance(item, dict):
                try:
                    returned_oid = int(item.get('id') or item.get('orderId') or oid)
                    for o in self.active_orders:
                        try:
                            if int(o.get('id') or 0) == int(returned_oid):
                                o['status'] = item.get('status') or o.get('status') or 'Closed'
                                o['market_price'] = float(item.get('marketPrice') or o.get('market_price') or 0)
                                o['market_value'] = float(item.get('marketValue') or o.get('market_value') or 0)
                                o['commission'] = float(item.get('commission') or o.get('commission') or 0)
                                # profit key may be named differently
                                try:
                                    o['pl'] = float(item.get('profitOrLoss') or o.get('pl') or 0)
                                except Exception:
                                    o['pl'] = o.get('pl', 0)
                                try:
                                    self._notify_listeners({'id': returned_oid, 'closed': True, 'payload': item})
                                except Exception:
                                    pass
                                break
                        except Exception:
                            LOG.exception("Error updating order entry in cache for %s", returned_oid)
                except Exception:
                    LOG.exception("Failed updating local cache after close for %s", returned_oid)

            return True
        except Exception:
            LOG.exception("Exception while closing order %s", order_id)
            return False

    def fetch_history(self, account_id: int = 0, page_number: int = 1, page_size: int = 1000):
        """Fetch historic/closed orders for the given account from history endpoint.

        Returns list of normalized order dicts or empty list on failure.
        """
        # Resolve account id fallback
        if not account_id:
            try:
                if CanonicalAppStore:
                    cur = CanonicalAppStore.instance().get_current_account()
                    account_id = cur.get('account_id') or cur.get('accountId') or cur.get('id') or 0
            except Exception:
                account_id = 0

        url = API_ORDERS_HISTORY.format(accountId=int(account_id or 0))

        headers = {}
        try:
            token = get_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        except Exception:
            LOG.debug("No auth token available when fetching history")
        headers.setdefault('Referer', API_BASE_URL)

        try:
            LOG.info("Fetching order history: url=%s account=%s", url, account_id)
            resp = requests.get(url, params={'PageNumber': int(page_number), 'PageSize': int(page_size)}, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            LOG.info("Order history GET response: status=%s", getattr(resp, 'status_code', None))
            try:
                data = resp.json()
            except Exception:
                LOG.debug("Order history GET response text: %s", getattr(resp, 'text', None))
                data = []

            # Normalize payload similar to fetch_orders
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # try common wrapper shapes
                if 'data' in data and isinstance(data.get('data'), list):
                    items = data.get('data')
                else:
                    for k in ('items', 'results', 'orders', 'value', 'payload'):
                        v = data.get(k)
                        if isinstance(v, list):
                            items = v
                            break

            # Debug: log a small sample of raw items to help diagnose missing fields
            try:
                LOG.debug("Order history raw sample (first 3): %s", items[:3])
                if items and isinstance(items, list) and len(items) > 0:
                    sample_keys = [list(i.keys()) for i in items[:1] if isinstance(i, dict)]
                    LOG.debug("Order history sample keys: %s", sample_keys)
            except Exception:
                pass

            normalized = []
            for item in items:
                try:
                    entry_price = (
                        item.get('entryPrice') or item.get('executedPrice') or
                        item.get('entryPriceForPendingOrder') or item.get('marketPrice') or 0
                    )
                    market_price = item.get('marketPrice') or entry_price or 0
                    try:
                        entry_price = float(entry_price)
                    except Exception:
                        entry_price = 0.0
                    try:
                        market_price = float(market_price)
                    except Exception:
                        market_price = 0.0

                    lot = float(item.get('lot') or item.get('lotSize') or item.get('volume') or 0)

                    order = {
                        'id': item.get('id') or item.get('orderId') or 0,
                        'time': item.get('createdAt') or item.get('orderClosedAt') or item.get('closed_time') or item.get('closedDate') or '',
                        'type': item.get('orderType') or item.get('type') or '',
                        'symbol': item.get('symbol') or '',
                        'lot': lot,
                        'entry_price': entry_price,
                        'entry_value': float(entry_price) * lot if entry_price and lot else 0.0,
                        'sl': item.get('stopLoss', 0),
                        'tp': item.get('takeProfit', 0),
                        'market_price': market_price,
                        'market_value': float(market_price) * lot if market_price and lot else 0.0,
                        'swap': item.get('swap', 0.0),
                        'commission': item.get('commission', 0.0),
                        'pl': item.get('profitOrLoss') or item.get('pl') or 0.0,
                        'pl_pct': item.get('profitOrLossInPercentage') or item.get('pl_pct') or 0.0,
                        # closed fields (history-specific)
                        'closed_time': item.get('closedAt') or item.get('orderClosedAt') or item.get('closed_time') or item.get('closedDate') or '',
                        'closed_price': item.get('closedPrice') or item.get('closed_price') or item.get('closePrice') or 0.0,
                        'closed_value': item.get('closedValue') or item.get('closed_value') or item.get('closeValue') or 0.0,
                        'remarks': item.get('remark') or item.get('remarks') or '',
                    }
                    normalized.append(order)
                except Exception:
                    LOG.exception("Failed to normalize history item: %s", item)

            # Cache and return
            self.order_history = list(normalized)
            LOG.info("Fetched %s history items for account %s", len(self.order_history), account_id)
            return list(self.order_history)
        except Exception:
            LOG.exception("Failed fetching order history from %s", url)
            return []