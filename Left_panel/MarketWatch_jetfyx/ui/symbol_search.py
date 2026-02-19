from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex
from PySide6.QtWidgets import QListView, QStyledItemDelegate, QStyle
from PySide6.QtGui import QPainter, QColor


# ---------- Model ----------
class SymbolSearchModel(QAbstractListModel):
    def __init__(self, symbol_manager):
        super().__init__()
        self.sm = symbol_manager
        self.items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role):
        item = self.items[index.row()]
        if role == Qt.DisplayRole:
            return f"{item['symbol']} - {item['name']}"
        if role == Qt.UserRole:
            return item

    def filter(self, text: str):
        text = text.strip().upper()
        all_symbols = self.sm.get_all_symbols()

        if not text:
            self.items = []
        else:
            self.items = [
                {
                    "symbol": s["symbol"],
                    "name": s.get("name", s["symbol"]),
                    "is_favorite": self.sm.is_favorite(s["symbol"]),
                }
                for s in all_symbols
                if text in s["symbol"] or text in s.get("name", "").upper()
            ]

        self.beginResetModel()
        self.endResetModel()


# ---------- Delegate ----------
class SymbolSearchDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        item = index.data(Qt.UserRole)
        rect = option.rect

        if option.state & QStyle.State_MouseOver:
            painter.fillRect(rect, QColor("#f1f5f9"))

        painter.setPen(QColor("#111"))
        painter.drawText(
            rect.adjusted(10, 0, -40, 0),
            Qt.AlignVCenter | Qt.AlignLeft,
            f"{item['symbol']} - {item['name']}",
        )

        star = "⭐" if item["is_favorite"] else "☆"
        painter.drawText(
            rect.adjusted(rect.width() - 30, 0, -10, 0),
            Qt.AlignVCenter | Qt.AlignRight,
            star,
        )
        painter.restore()


# ---------- Dropdown ----------
class SymbolSearchDropdown(QListView):
    def __init__(self, parent_widget):
        super().__init__(None)
        self.parent_widget = parent_widget
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setMaximumHeight(260)
