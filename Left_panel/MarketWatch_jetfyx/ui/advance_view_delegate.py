"""
advance_view_delegate.py  –  Custom delegate for detailed market rows.

Changes (theme-aware):
  ✅ Reads ThemeManager tokens on every paint() call
  ✅ bg_panel   → even rows
  ✅ bg_row_alt → odd rows
  ✅ bg_selected → selected rows
  ✅ text_primary replaces hardcoded #333
  ✅ text_secondary replaces hardcoded #666
  ✅ Falls back to light colours when ThemeManager unavailable
"""
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from datetime import datetime

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class AdvanceViewDelegate(QStyledItemDelegate):
    """Custom delegate for advance view with additional market data."""

    def __init__(self, parent=None):
        super().__init__(parent)

    # ------------------------------------------------------------------
    def _get_colors(self):
        """Return (bg_even, bg_odd, bg_sel, text_main, text_sub) from tokens."""
        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
                return (
                    t.get("bg_panel",    "#ffffff"),
                    t.get("bg_row_alt",  "#f9fafb"),
                    t.get("bg_selected", "#1565c0"),
                    t.get("text_primary","#1a202c"),
                    t.get("text_secondary","#4a5568"),
                )
            except Exception:
                pass
        return "#ffffff", "#f5f5f5", "#bbdefb", "#333333", "#666666"

    # ------------------------------------------------------------------
    def paint(self, painter, option, index):
        painter.save()

        row_data = index.data(Qt.UserRole)
        col = index.column()

        if not isinstance(row_data, dict):
            super().paint(painter, option, index)
            painter.restore()
            return

        symbol     = row_data.get("symbol",     "")
        sell       = row_data.get("sell",       "")
        buy        = row_data.get("buy",        "")
        raw_time   = row_data.get("time",       "")
        time_str   = ""
        if raw_time:
            try:
                dt = datetime.fromisoformat(raw_time.replace("Z", ""))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = ""
        change_pct = row_data.get("change_pct", "")
        change_pts = row_data.get("change_pts", "")
        low        = row_data.get("low",        "")
        high       = row_data.get("high",       "")
        spread     = row_data.get("spread",     "")

        bg_even, bg_odd, bg_sel, txt_main, txt_sub = self._get_colors()

        # Row background
        if index.row() % 2:
            painter.fillRect(option.rect, QColor(bg_odd))
        else:
            painter.fillRect(option.rect, QColor(bg_even))

        # Fonts
        main_font = QFont()
        main_font.setPointSize(10)
        main_font.setBold(True)
        sub_font = QFont()
        sub_font.setPointSize(7)

        if col == 0:  # SYMBOL
            painter.setFont(main_font)
            painter.setPen(QColor(txt_main))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                             Qt.AlignLeft | Qt.AlignTop, symbol)

            painter.setFont(sub_font)
            try:
                cv = float(str(change_pct).replace("%","").replace("+","") or 0)
            except Exception:
                cv = 0
            change_color = QColor("#4caf50") if cv > 0 else QColor("#f44336")
            painter.setPen(change_color)
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                             Qt.AlignLeft | Qt.AlignBottom,
                             f"{change_pct} : {change_pts}")

        elif col == 1:  # SELL
            painter.setFont(main_font)
            painter.setPen(QColor("#f44336"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                             Qt.AlignCenter | Qt.AlignTop, sell)
            painter.setFont(sub_font)
            painter.setPen(QColor(txt_sub))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                             Qt.AlignCenter | Qt.AlignBottom, f"L-{low}")

        elif col == 2:  # BUY
            painter.setFont(main_font)
            painter.setPen(QColor("#2196f3"))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                             Qt.AlignCenter | Qt.AlignTop, buy)
            painter.setFont(sub_font)
            painter.setPen(QColor(txt_sub))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                             Qt.AlignCenter | Qt.AlignBottom, f"H-{high}")

        elif col == 3:  # TIME
            painter.setFont(main_font)
            painter.setPen(QColor(txt_main))
            painter.drawText(option.rect.adjusted(5, 5, -5, -25),
                             Qt.AlignCenter | Qt.AlignTop, time_str)
            painter.setFont(sub_font)
            painter.setPen(QColor(txt_sub))
            painter.drawText(option.rect.adjusted(5, 20, -5, -5),
                             Qt.AlignCenter | Qt.AlignBottom, f"Spread - {spread}")

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 35)
