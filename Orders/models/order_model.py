from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
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
            "ID":           "id",
            "Time":         "time",
            "Type":         "type",
            "Symbol":       "symbol",
            "Lot Size":     "lot",
            "Entry Price":  "entry_price",
            "Entry Value":  "entry_value",
            "S/L":          "sl",
            "T/P":          "tp",
            "Market Price": "market_price",
            "Market Value": "market_value",
            "SWAP":         "swap",
            "Commission":   "commission",
            "PROFIT/LOSS":  "pl",
            "P/L IN %":     "pl_pct",
            "Remarks":      "remarks",
        }

        if role == Qt.DisplayRole:
            if column == "Actions":
                return ""
            val = order.get(key_map.get(column, ""), "")
            return "" if val is None else str(val)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.ForegroundRole:
            try:
                from Theme.theme_manager import ThemeManager
                tok = ThemeManager.instance().tokens()
                accent   = QColor(tok.get("accent", "#1976d2"))
                text_pri = QColor(tok.get("text_primary", "#1a202c"))
            except Exception:
                accent   = QColor("#1976d2")
                text_pri = QColor("#1a202c")

            if column in ["PROFIT/LOSS", "P/L IN %"]:
                try:
                    val = float(order.get("pl", 0))
                    return QColor("#22c55e") if val >= 0 else QColor("#ef4444")
                except Exception:
                    return text_pri
            elif column in ["Symbol", "Type", "ID"]:
                return accent
            else:
                return text_pri

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def add_order(self, order: dict):
        row = len(self.orders)
        LOG.debug("OrderModel.add_order inserting at row %s id=%s", row, order.get('id'))

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

        # Derived values
        try:
            order['entry_value'] = order['entry_price'] * order['lot']
        except Exception:
            order['entry_value'] = 0.0
        try:
            order['market_value'] = order['market_price'] * order['lot']
        except Exception:
            order['market_value'] = 0.0

        order.setdefault('pl', 0.0)
        order.setdefault('pl_pct', 0.0)

        self.beginInsertRows(QModelIndex(), row, row)
        self.orders.append(order)
        self.endInsertRows()
        LOG.info("OrderModel added order id=%s symbol=%s total_rows=%s",
                 order.get('id'), order.get('symbol'), len(self.orders))

    def remove_order_by_id(self, order_id):
        try:
            oid = int(order_id)
        except Exception:
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
        """Update market_price and market_value for all orders matching symbol."""
        try:
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

        changed_rows = []
        for idx, order in enumerate(self.orders):
            try:
                if (order.get('symbol') or '').upper() != (symbol or '').upper():
                    continue
                order['market_price'] = float(mid)
                # FIX: compute market_value = market_price × lot
                order['market_value'] = order['market_price'] * float(order.get('lot') or 0)
                changed_rows.append(idx)
            except Exception:
                LOG.exception("Failed updating market price for order index %s", idx)

        if not changed_rows:
            return

        first, last = min(changed_rows), max(changed_rows)
        top_left     = self.index(first, 0)
        bottom_right = self.index(last, self.columnCount() - 1)
        try:
            self.dataChanged.emit(top_left, bottom_right, [])
        except Exception:
            try:
                self.layoutChanged.emit()
            except Exception:
                LOG.exception("Failed emitting dataChanged after price update")

    def update_order_from_backend(self, order_update: dict):
        """Update an order with real-time data from backend (WebSocket/SignalR)."""
        if not order_update or 'id' not in order_update:
            LOG.warning("update_order_from_backend: invalid order_update (missing id)")
            return

        order_id = order_update.get('id')
        LOG.info("[OrderModel] Received update for order %s: market_price=%s, pl=%s, pl_pct=%s",
                 order_id, order_update.get('market_price'),
                 order_update.get('pl'), order_update.get('pl_pct'))

        for idx, order in enumerate(self.orders):
            if order.get('id') == order_id:
                try:
                    if 'market_price' in order_update:
                        order['market_price'] = float(order_update['market_price'])

                    # FIX: compute market_value = market_price × lot
                    order['market_value'] = order['market_price'] * float(order.get('lot') or 0)

                    # P&L from backend (authoritative)
                    if 'pl' in order_update:
                        order['pl'] = float(order_update['pl'])
                    if 'pl_pct' in order_update:
                        order['pl_pct'] = float(order_update['pl_pct'])

                    if 'swap' in order_update:
                        order['swap'] = float(order_update['swap'])
                    if 'commission' in order_update:
                        order['commission'] = float(order_update['commission'])

                    for field in ['remarks', 'time']:
                        if field in order_update:
                            order[field] = order_update[field]

                    LOG.debug("Updated order %s: market_price=%.5f, market_value=%.5f, pl=%.2f, pl_pct=%.2f",
                              order_id, order.get('market_price', 0),
                              order.get('market_value', 0),
                              order.get('pl', 0), order.get('pl_pct', 0))

                    top_left     = self.index(idx, 0)
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