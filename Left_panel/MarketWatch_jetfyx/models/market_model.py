from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont


class MarketModel(QAbstractTableModel):
    """
    High-performance market table model
    - Dict-based rows only
    - Row-level updates (no UI rebuilds)
    """

    HEADERS_NORMAL = ["SYMBOL", "SELL", "BUY"]
    HEADERS_ADVANCE = ["SYMBOL", "SELL", "BUY", "TIME"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: list[dict] = []
        self.advance_view = False

        # 🔥 fast lookup: symbol → row index
        self._row_by_symbol = {}

    # --------------------------------------------------
    # Qt required
    # --------------------------------------------------

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers())

    def headers(self):
        return self.HEADERS_ADVANCE if self.advance_view else self.HEADERS_NORMAL

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            try:
                return self.headers()[section]
            except IndexError:
                return None
        return section + 1

    # --------------------------------------------------
    # DATA (CRASH-SAFE)
    # --------------------------------------------------

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.rows):
            return None

        item = self.rows[row]

        # ==========================
        # CATEGORY ROW
        # ==========================
        if item.get("category"):
            if role == Qt.DisplayRole:
                if col == 0:
                    return f"{item['arrow']}  {item['display']} ({item['count']})"
                return ""

            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font

            return None

        # ==========================
        # SYMBOL ROW
        # ==========================
        if role == Qt.DisplayRole:
            if col == 0:
                return item.get("symbol", "")
            elif col == 1:
                return item.get("sell", "")
            elif col == 2:
                return item.get("buy", "")
            elif col == 3:
                raw_time = item.get("time", "")
                if raw_time:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(raw_time.replace("Z", ""))
                        return dt.strftime("%H:%M:%S")
                    except Exception:
                        return ""
                return ""

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.UserRole:
            return item

        return None

    def flags(self, index):
        """Ensure items are not editable via the model.

        This explicitly removes Qt.ItemIsEditable so delegates/editors
        are not created on click or programmatic focus attempts.
        """
        if not index.isValid():
            return Qt.NoItemFlags

        row = index.row()
        if row >= len(self.rows):
            return Qt.NoItemFlags

        item = self.rows[row]

        # Category rows: not selectable nor editable
        if item.get("category"):
            return Qt.ItemIsEnabled

        # Symbol rows: selectable + enabled, but not editable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # --------------------------------------------------
    # VIEW MODES
    # --------------------------------------------------

    def set_advance_view(self, enabled: bool):
        if self.advance_view == enabled:
            return

        self.beginResetModel()
        self.advance_view = enabled
        self.endResetModel()

    # --------------------------------------------------
    # FULL DATA LOAD (ONCE)
    # --------------------------------------------------

    def set_rows(self, rows: list[dict]):
        """
        Used ONLY on first load or category rebuild
        """
        self.beginResetModel()
        self.rows = rows
        self._row_by_symbol.clear()

        for i, r in enumerate(rows):
            if "symbol" in r:
                self._row_by_symbol[r["symbol"]] = i

        self.endResetModel()

    # --------------------------------------------------
    # 🔥 LIVE UPDATE (REACT STYLE)
    # --------------------------------------------------

    def update_symbol(self, symbol_data: dict):
        """
        Update a single symbol row
        """
        symbol = symbol_data.get("symbol")
        if not symbol:
            return

        row = self._row_by_symbol.get(symbol)

        # ➕ NEW SYMBOL
        if row is None:
            row = len(self.rows)
            self.beginInsertRows(QModelIndex(), row, row)
            self.rows.append(symbol_data)
            self._row_by_symbol[symbol] = row
            self.endInsertRows()
            return

        # 🔄 UPDATE EXISTING (NO REBUILD)
        self.rows[row].update(symbol_data)

        left = self.index(row, 0)
        right = self.index(row, self.columnCount() - 1)

        self.dataChanged.emit(left, right, [
            Qt.DisplayRole,
            Qt.TextAlignmentRole,
            Qt.UserRole
        ])
