from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtCore import Qt


def _hover_color() -> QColor:
    """Return the hover row background colour from the current theme."""
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()
        c = tok.get("bg_row_hover", "transparent")
        if c and c != "transparent":
            return QColor(c)
    except Exception:
        pass
    return QColor("#e3f2fd")   # fallback light blue


class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def paint(self, painter, option, index):
        row = index.row()

        # Hover background (not applied when row is selected)
        if (
            row == self.table.hovered_row
            and not (option.state & QStyle.State_Selected)
        ):
            hc = _hover_color()
            if hc.isValid() and hc.alpha() > 0:
                painter.fillRect(option.rect, hc)

        super().paint(painter, option, index)

        # Draw hover star on rightmost column when table allows it
        try:
            if row == self.table.hovered_row and getattr(self.table, 'show_hover_favorite', True):
                symbol = None
                try:
                    symbol = self.table.get_symbol_at_row(row)
                except Exception:
                    pass

                if symbol:
                    is_fav = False
                    try:
                        if getattr(self.table, 'symbol_manager', None):
                            is_fav = self.table.symbol_manager.is_favorite(symbol)
                    except Exception:
                        pass

                    star = "★" if is_fav else "☆"
                    painter.save()
                    font = QFont(); font.setPointSize(12)
                    painter.setFont(font)
                    color = QColor('#ffa500') if is_fav else QColor('#999')
                    painter.setPen(color)
                    r = option.rect
                    x = r.right() - 24
                    y = r.top() + (r.height() + painter.fontMetrics().ascent()) // 2 - 2
                    painter.drawText(x, y, star)
                    painter.restore()
        except RuntimeError:
            pass