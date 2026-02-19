"""
Advance View Delegate - Custom delegate for showing detailed market information
"""
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QRect, QSize

from PySide6.QtGui import QPainter, QFont, QColor, QPen
from datetime import datetime


class AdvanceViewDelegate(QStyledItemDelegate):
    """Custom delegate for advance view with additional market data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Custom paint for advance view cells"""
        painter.save()
        
        # Get full row data
        row_data = index.data(Qt.UserRole)
        col = index.column()

        # Support dict-based row_data (new structure)
        if not isinstance(row_data, dict):
            super().paint(painter, option, index)
            painter.restore()
            return


        symbol      = row_data.get("symbol", "")
        sell        = row_data.get("sell", "")
        buy         = row_data.get("buy", "")
        raw_time    = row_data.get("time", "")
        time        = ""
        if raw_time:
            try:
                dt = datetime.fromisoformat(raw_time.replace("Z", ""))
                time = dt.strftime("%H:%M:%S")
            except Exception:
                time = ""
        change_pct  = row_data.get("change_pct", "")
        change_pts  = row_data.get("change_pts", "")
        low         = row_data.get("low", "")
        high        = row_data.get("high", "")
        spread      = row_data.get("spread", "")
        
        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#bbdefb"))
        elif index.row() % 2:
            painter.fillRect(option.rect, QColor("#f5f5f5"))
        else:
            painter.fillRect(option.rect, QColor("#ffffff"))
        
        # Set up fonts
        main_font = QFont()
        main_font.setPointSize(10)
        main_font.setBold(True)
        
        sub_font = QFont()
        sub_font.setPointSize(7)
        
        if col == 0:  # SYMBOL column
            # Draw symbol name
            painter.setFont(main_font)
            painter.setPen(QColor("#333"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25), 
                           Qt.AlignLeft | Qt.AlignTop, symbol)

            # Draw percentage and change points
            painter.setFont(sub_font)
            try:
                change_val = float(str(change_pct).replace("%", "").replace("+", "").replace("-", "-") or 0)
            except Exception:
                change_val = 0
            change_color = QColor("#4caf50") if change_val > 0 else QColor("#f44336")
            painter.setPen(change_color)
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                           Qt.AlignLeft | Qt.AlignBottom, 
                           f"{change_pct} : {change_pts}")

        elif col == 1:  # SELL column
            # Draw sell price
            painter.setFont(main_font)
            painter.setPen(QColor("#f44336"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                           Qt.AlignCenter | Qt.AlignTop, sell)

            # Draw low value
            painter.setFont(sub_font)
            painter.setPen(QColor("#666"))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                           Qt.AlignCenter | Qt.AlignBottom, 
                           f"L-{low}")

        elif col == 2:  # BUY column
            # Draw buy price
            painter.setFont(main_font)
            painter.setPen(QColor("#2196f3"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                           Qt.AlignCenter | Qt.AlignTop, buy)

            # Draw high value
            painter.setFont(sub_font)
            painter.setPen(QColor("#666"))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                           Qt.AlignCenter | Qt.AlignBottom, 
                           f"H-{high}")

        elif col == 3:  # TIME column
            # Draw time
            painter.setFont(main_font)
            painter.setPen(QColor("#333"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                           Qt.AlignCenter | Qt.AlignTop, time)

            # Draw spread
            painter.setFont(sub_font)
            painter.setPen(QColor("#666"))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                           Qt.AlignCenter | Qt.AlignBottom, 
                           f"Spread - {spread}")

        painter.restore()
    
    def sizeHint(self, option, index):
        """Return size hint for cells"""
        # Taller rows to accommodate two lines of text
        return QSize(option.rect.width(), 35)
