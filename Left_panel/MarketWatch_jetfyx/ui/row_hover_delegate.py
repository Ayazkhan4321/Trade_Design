from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtCore import Qt

class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def paint(self, painter, option, index):
        row = index.row()

        # Hover row background (only if NOT selected)
        if (
            row == self.table.hovered_row
            and not (option.state & QStyle.State_Selected)
        ):
            painter.fillRect(option.rect, QColor("#e3f2fd"))

        super().paint(painter, option, index)

        # Draw hover star on the right when this row is hovered and represents a symbol
        try:
            # Only draw hover star if the table allows it (favorites table disables it)
            if row == self.table.hovered_row and getattr(self.table, 'show_hover_favorite', True):
                # Get symbol for this row (table exposes helper)
                symbol = None
                try:
                    symbol = self.table.get_symbol_at_row(row)
                except Exception:
                    symbol = None

                if symbol:
                    is_fav = False
                    try:
                        if getattr(self.table, 'symbol_manager', None):
                            is_fav = self.table.symbol_manager.is_favorite(symbol)
                    except Exception:
                        is_fav = False

                    star = "★" if is_fav else "☆"
                    # Prepare painter
                    painter.save()
                    font = QFont()
                    font.setPointSize(12)
                    painter.setFont(font)
                    color = QColor('#ffa500') if is_fav else QColor('#999')
                    painter.setPen(color)

                    r = option.rect
                    # Position star 24px from right, vertically centered
                    x = r.right() - 24
                    y = r.top() + (r.height() + painter.fontMetrics().ascent()) // 2 - 2

                    painter.drawText(x, y, star)
                    painter.restore()
        except RuntimeError:
            # Defensive: item may be gone
            pass
