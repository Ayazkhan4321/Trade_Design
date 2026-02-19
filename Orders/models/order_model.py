from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
import logging

LOG = logging.getLogger(__name__)


class OrderModel(QAbstractTableModel):

    headers = [
        "ID", "Time", "Type", "Symbol",
        "Lot Size", "Entry Price", "Entry Value",
        "S/L", "T/P",
        "Market Price", "Market Value",
        "SWAP", "Commission",
        "PROFIT/LOSS", "P/L IN %",
        "Actions", "Remarks"
    ]

    def __init__(self):
        super().__init__()
        # start with an empty list — orders will be populated from backend or
        # through runtime events. Tests and fixtures can still directly set
        # `self.orders` if needed.
        self.orders = []

    def rowCount(self, parent=None):
        return len(self.orders)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None

        order = self.orders[index.row()]
        column = self.headers[index.column()]

        key_map = {
            "ID": "id",
            "Time": "time",
            "Type": "type",
            "Symbol": "symbol",
            "Lot Size": "lot",
            "Entry Price": "entry_price",
            "Entry Value": "entry_value",
            "S/L": "sl",
            "T/P": "tp",
            "Market Price": "market_price",
            "Market Value": "market_value",
            "SWAP": "swap",
            "Commission": "commission",
            "PROFIT/LOSS": "pl",
            "P/L IN %": "pl_pct",
            "Remarks": "remarks"
        }

        if role == Qt.DisplayRole:
            if column == "Actions":
                return ""  # handled later via delegate
            val = order.get(key_map.get(column, ""), "")
            # Format None as empty string
            return "" if val is None else str(val)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.ForegroundRole:
            if column in ["PROFIT/LOSS", "P/L IN %"]:
                try:
                    return Qt.green if float(order.get("pl", 0)) > 0 else Qt.red
                except Exception:
                    return None

        return None

    def flags(self, index):
        """Make cells selectable and enabled but not editable."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
    def add_order(self, order: dict):
        """Append a new order dict and notify views.

        The incoming `order` dict is expected to contain keys that roughly
        match the internal key names used in `key_map` above (id, time, type,
        symbol, lot, entry_price, market_price, etc). This method will insert
        the row and emit the necessary signals for the view to update.
        """
        row = len(self.orders)
        LOG.debug("OrderModel.add_order inserting at row %s id=%s", row, order.get('id'))
        
        # Ensure numeric types for computation
        try:
            order['lot'] = float(order.get('lot') or 0)
        except Exception:
            order['lot'] = 0.0
        try:
            order['entry_price'] = float(order.get('entry_price') or 0)
        except Exception:
            order['entry_price'] = 0.0
        try:
            order['market_price'] = float(order.get('market_price') or 0)
        except Exception:
            order['market_price'] = 0.0

        # Compute derived values if possible
        try:
            order['entry_value'] = float(order.get('entry_price', 0)) * float(order.get('lot', 0))
        except Exception:
            order['entry_value'] = 0.0
        try:
            order['market_value'] = float(order.get('market_price', 0)) * float(order.get('lot', 0))
        except Exception:
            order['market_value'] = 0.0

        # Initial P/L (may be zero until market updates arrive)
        order['pl'] = 0.0
        order['pl_pct'] = 0.0

        self.beginInsertRows(QModelIndex(), row, row)
        self.orders.append(order)
        self.endInsertRows()
        LOG.info("OrderModel added order id=%s symbol=%s total_rows=%s", order.get('id'), order.get('symbol'), len(self.orders))


    def remove_order_by_id(self, order_id):
        """Remove an order from the model by its id (if present) and notify views."""
        try:
            oid = int(order_id)
        except Exception:
            # invalid id -> nothing to remove
            return False

        for idx, o in enumerate(self.orders):
            try:
                if int(o.get('id') or 0) == oid:
                    self.beginRemoveRows(QModelIndex(), idx, idx)
                    self.orders.pop(idx)
                    self.endRemoveRows()
                    LOG.info("OrderModel removed order id=%s at row=%s", oid, idx)
                    return True
            except Exception:
                LOG.exception("Failed removing order id=%s at index %s", oid, idx)
        return False


    def clear_orders(self):
        self.beginResetModel()
        self.orders = []
        self.endResetModel()
    def update_market_price(self, symbol: str, sell: str, buy: str):
        """Update market_price for all orders matching `symbol`.

        `sell` and `buy` are string representations (as emitted by SymbolManager).
        We compute mid = (sell + buy) / 2 and update ONLY market_price.
        
        ⚠️ IMPORTANT: P/L values come from backend WebSocket only.
        We NEVER recalculate P/L locally - that overwrites backend values.
        """
        try:
            # try to parse numeric sell/buy; fall back to float(order['market_price']) if parsing fails
            s = float(sell) if (sell is not None and str(sell).strip() != "") else None
        except Exception:
            s = None
        try:
            b = float(buy) if (buy is not None and str(buy).strip() != "") else None
        except Exception:
            b = None

        if s is None and b is None:
            return

        if s is None:
            mid = b
        elif b is None:
            mid = s
        else:
            mid = (s + b) / 2.0

        if mid is None:
            return

        # Update matching orders and collect changed row indices
        changed_rows = []
        for idx, order in enumerate(self.orders):
            try:
                if (order.get('symbol') or '').upper() != (symbol or '').upper():
                    continue
                
                # Update ONLY market_price - nothing else
                order['market_price'] = float(mid)
                order['market_value'] = 0.0  # Backend-owned, not calculated
                # ❌ DO NOT recalculate pl or pl_pct - they come from backend WebSocket
                
                changed_rows.append(idx)
            except Exception:
                LOG.exception("Failed updating market price for order index %s", idx)

        # Emit dataChanged for contiguous ranges for performance
        if not changed_rows:
            return

        first = min(changed_rows)
        last = max(changed_rows)
        top_left = self.index(first, 0)
        bottom_right = self.index(last, self.columnCount() - 1)
        try:
            self.dataChanged.emit(top_left, bottom_right, [])
        except Exception:
            try:
                # Fallback: full layout change
                self.layoutChanged.emit()
            except Exception:
                LOG.exception("Failed emitting dataChanged/layoutChanged after price update")

    def update_order_from_backend(self, order_update: dict):
        """
        Update an order with real-time data from backend (WebSocket/SignalR).
        
        Backend sends the authoritative values - we just display them as-is:
        - market_price: current market price from backend
        - market_value: set to 0 (not used)
        - pl: profit/loss amount from backend
        - pl_pct: profit/loss percentage from backend
        - swap: current swap value
        - commission: current commission
        """
        if not order_update or 'id' not in order_update:
            LOG.warning("update_order_from_backend: invalid order_update (missing id)")
            return
        
        order_id = order_update.get('id')
        LOG.info("[OrderModel] Received update for order %s: market_price=%s, pl=%s, pl_pct=%s", 
                 order_id, order_update.get('market_price'), 
                 order_update.get('pl'), order_update.get('pl_pct'))
        
        # Find order in model
        for idx, order in enumerate(self.orders):
            if order.get('id') == order_id:
                try:
                    # Update fields directly from backend - no calculations
                    if 'market_price' in order_update:
                        order['market_price'] = float(order_update['market_price'])
                    
                    # Market value is always 0 (backend doesn't send it, we don't calculate it)
                    order['market_value'] = 0.0
                    
                    # P&L values from backend (authoritative)
                    if 'pl' in order_update:
                        order['pl'] = float(order_update['pl'])
                    if 'pl_pct' in order_update:
                        order['pl_pct'] = float(order_update['pl_pct'])
                    
                    # Swap and commission from backend
                    if 'swap' in order_update:
                        order['swap'] = float(order_update['swap'])
                    if 'commission' in order_update:
                        order['commission'] = float(order_update['commission'])
                    
                    # Update other string fields if present
                    for field in ['remarks', 'time']:
                        if field in order_update:
                            order[field] = order_update[field]
                    
                    LOG.debug("Updated order %s: market_price=%.5f, market_value=0.0, pl=%.2f, pl_pct=%.2f",
                              order_id, order.get('market_price', 0), 
                              order.get('pl', 0), order.get('pl_pct', 0))
                    
                    # Emit dataChanged for this row to refresh table display
                    top_left = self.index(idx, 0)
                    bottom_right = self.index(idx, self.columnCount() - 1)
                    try:
                        self.dataChanged.emit(top_left, bottom_right, [])
                    except Exception:
                        LOG.exception("Failed emitting dataChanged after order update")
                    
                    return
                except Exception:
                    LOG.exception("Error updating order %s", order_id)
                    return
        
        LOG.warning("Order %s not found in model for update", order_id)

    def update_height(self):
        rows = self.model.rowCount()
        header = self.horizontalHeader().height()
        row_h = self.verticalHeader().defaultSectionSize()
        self.setMaximumHeight(header + (rows * row_h) + 2)
