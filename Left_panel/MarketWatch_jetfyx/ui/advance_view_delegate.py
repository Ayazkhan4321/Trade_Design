"""
advance_view_delegate.py  –  Custom delegate for detailed market rows.

  ✅ Reads ThemeManager tokens on every paint() call
  ✅ Shows ★/☆ on the TIME column when row is hovered (replaces time text)
  ✅ Full theme-aware colours
"""
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from datetime import datetime

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class AdvanceViewDelegate(QStyledItemDelegate):

    def __init__(self, table=None):
        super().__init__(table)
        self.table = table   # store explicit ref — self.parent() is unreliable in delegates

    # ── Colour helpers ────────────────────────────────────────────────────────
    def _get_colors(self):
        """Return (bg_even, bg_odd, bg_sel, text_main, text_sub, bg_hover).
        Reads directly from ThemeManager tokens — theme_state.py now sets
        bg_row_hover correctly for every theme including crazy variants."""
        # 1. Pushed directly by market_widget.apply_theme
        pushed = getattr(self, 'hover_color', None)

        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
                bg_panel = t.get("bg_panel",      "#ffffff")
                bg_alt   = t.get("bg_row_alt",    "#f9fafb")
                bg_sel   = t.get("bg_selected",   "#1565c0")
                txt_main = t.get("text_primary",  "#1a202c")
                txt_sub  = t.get("text_secondary","#4a5568")
                # Hover: pushed > token
                hover = pushed or t.get("bg_row_hover", "#e8f5e9")
                return bg_panel, bg_alt, bg_sel, txt_main, txt_sub, hover
            except Exception:
                pass
        return "#ffffff", "#f5f5f5", "#bbdefb", "#333333", "#666666", pushed or "#e8f5e9"

    # ── Paint ─────────────────────────────────────────────────────────────────
    def paint(self, painter, option, index):
        painter.save()

        col = index.column()

        # UserRole data is only set on col 0 — always read from there
        try:
            col0_index = index.model().index(index.row(), 0)
            row_data   = col0_index.data(Qt.UserRole)
        except Exception:
            row_data = index.data(Qt.UserRole)

        if not isinstance(row_data, dict):
            # Still need to handle hover star even if no UserRole dict
            # (e.g. category/header rows — just paint normally)
            table   = self.table
            hovered = getattr(table, 'hovered_row', -1) if table else -1
            is_hovered = (index.row() == hovered)
            last_col = index.model().columnCount() - 1

            if is_hovered and col == last_col and getattr(table, 'show_hover_favorite', True):
                # Try to get symbol from table directly
                symbol = None
                try:
                    symbol = table.get_symbol_at_row(index.row())
                except Exception:
                    pass
                if symbol:
                    is_fav = False
                    try:
                        sm = getattr(table, 'symbol_manager', None)
                        if sm:
                            is_fav = sm.is_favorite(symbol)
                    except Exception:
                        pass
                    star  = "★" if is_fav else "☆"
                    color = QColor('#ffc107') if is_fav else QColor('#aaaaaa')
                    star_font = QFont(); star_font.setPointSize(16)
                    painter.setFont(star_font)
                    painter.setPen(color)
                    painter.drawText(option.rect, Qt.AlignCenter, star)
                    painter.restore()
                    return

            super().paint(painter, option, index)
            painter.restore()
            return

        symbol     = row_data.get("symbol",     "")
        sell       = row_data.get("sell",        "")
        buy        = row_data.get("buy",         "")
        raw_time   = row_data.get("time",        "")
        time_str   = ""
        if raw_time:
            try:
                dt = datetime.fromisoformat(raw_time.replace("Z", ""))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = ""
        change_pct = row_data.get("change_pct", "")
        change_pts = row_data.get("change_pts", "")
        low        = row_data.get("low",         "")
        high       = row_data.get("high",        "")
        spread     = row_data.get("spread",      "")

        bg_even, bg_odd, bg_sel, txt_main, txt_sub, bg_hover = self._get_colors()

        # ── Row background ────────────────────────────────────────────────────
        table   = self.table
        hovered = getattr(table, 'hovered_row', -1) if table else -1
        is_hovered = (index.row() == hovered)

        # Skip all custom painting for the expanded trade panel row.
        # Two checks:
        #   1. expanded_row attribute (set after dataChanged, may be None on first paint)
        #   2. empty-dict pattern: market_table blanks all values when expanding
        is_expanded = (
            (table is not None and index.row() == getattr(table, 'expanded_row', None))
            or (symbol == "" and sell == "" and buy == "")
        )
        if is_expanded:
            # Paint nothing — TradePanel widget sits on top
            painter.restore()
            return

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(bg_sel))
        elif is_hovered:
            _hc = QColor(bg_hover); _hc.setAlpha(255)
            painter.fillRect(option.rect, _hc)
        elif index.row() % 2:
            painter.fillRect(option.rect, QColor(bg_odd))
        else:
            painter.fillRect(option.rect, QColor(bg_even))

        # ── Fonts ─────────────────────────────────────────────────────────────
        main_font = QFont(); main_font.setPointSize(10); main_font.setBold(True)
        sub_font  = QFont(); sub_font.setPointSize(7)

        # ── TIME column: show star on hover, time+spread otherwise ────────────
        if col == 3:
            show_star = (
                is_hovered
                and symbol
                and getattr(table, 'show_hover_favorite', True)
            )

            if show_star:
                is_fav = False
                try:
                    sm = getattr(table, 'symbol_manager', None)
                    if sm:
                        is_fav = sm.is_favorite(symbol)
                except Exception:
                    pass

                star  = "★" if is_fav else "☆"
                color = QColor('#ffc107') if is_fav else QColor('#aaaaaa')

                star_font = QFont(); star_font.setPointSize(16)
                painter.setFont(star_font)
                painter.setPen(color)
                painter.drawText(option.rect, Qt.AlignCenter, star)
            else:
                # Normal time + spread display
                painter.setFont(main_font)
                painter.setPen(QColor(txt_main))
                painter.drawText(
                    option.rect.adjusted(5, 5, -5, -25),
                    Qt.AlignCenter | Qt.AlignTop, time_str
                )
                painter.setFont(sub_font)
                painter.setPen(QColor(txt_sub))
                painter.drawText(
                    option.rect.adjusted(5, 20, -5, -5),
                    Qt.AlignCenter | Qt.AlignBottom, f"Spread - {spread}"
                )

        elif col == 0:  # SYMBOL
            painter.setFont(main_font)
            painter.setPen(QColor(txt_main))
            painter.drawText(
                option.rect.adjusted(5, 5, -5, -25),
                Qt.AlignLeft | Qt.AlignTop, symbol
            )
            painter.setFont(sub_font)
            try:
                cv = float(str(change_pct).replace("%","").replace("+","") or 0)
            except Exception:
                cv = 0
            change_color = QColor("#4caf50") if cv > 0 else QColor("#f44336")
            painter.setPen(change_color)
            painter.drawText(
                option.rect.adjusted(5, 20, -5, -5),
                Qt.AlignLeft | Qt.AlignBottom, f"{change_pct} : {change_pts}"
            )

        elif col == 1:  # SELL
            painter.setFont(main_font)
            painter.setPen(QColor("#f44336"))
            painter.drawText(
                option.rect.adjusted(5, 5, -5, -25),
                Qt.AlignCenter | Qt.AlignTop, sell
            )
            painter.setFont(sub_font)
            painter.setPen(QColor(txt_sub))
            painter.drawText(
                option.rect.adjusted(5, 20, -5, -5),
                Qt.AlignCenter | Qt.AlignBottom, f"L-{low}"
            )

        elif col == 2:  # BUY
            painter.setFont(main_font)
            painter.setPen(QColor("#2196f3"))
            painter.drawText(
                option.rect.adjusted(5, 5, -5, -25),
                Qt.AlignCenter | Qt.AlignTop, buy
            )
            painter.setFont(sub_font)
            painter.setPen(QColor(txt_sub))
            painter.drawText(
                option.rect.adjusted(5, 20, -5, -5),
                Qt.AlignCenter | Qt.AlignBottom, f"H-{high}"
            )

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 48)