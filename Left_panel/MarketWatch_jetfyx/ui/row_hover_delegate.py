from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtCore import Qt, QRect


def _hover_color(delegate=None) -> QColor:
    """Read bg_row_hover from the current theme — always correct now that
    theme_state.py sets it per-theme including all crazy variants."""
    # 1. Directly pushed by market_widget.apply_theme (most reliable)
    if delegate is not None:
        hc = getattr(delegate, 'hover_color', None)
        if hc:
            qc = QColor(hc)
            if qc.isValid():
                return qc
    # 2. Read from ThemeManager token
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()
        c = tok.get("bg_row_hover", "")
        if c and c not in ("transparent", ""):
            qc = QColor(c)
            if qc.isValid() and qc.alpha() > 0:
                return qc
    except Exception:
        pass
    # 3. Last resort
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        dark = app.palette().window().color().lightness() < 128 if app else False
    except Exception:
        dark = False
    return QColor("#2a3352") if dark else QColor("#e8f5e9")


class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def paint(self, painter, option, index):
        row = index.row()
        col = index.column()

        expanded = getattr(self.table, 'expanded_row', None)

        # ── ALWAYS strip Qt's built-in hover highlight — we draw it ourselves ─
        # This prevents State_MouseOver from leaking through super().paint() on
        # any code path, including after multiple panel open/close cycles.
        option.state &= ~QStyle.State_MouseOver

        # ── While a panel is open: plain paint only, no hover, no selection ───
        if expanded is not None:
            option.state &= ~QStyle.State_Selected
            super().paint(painter, option, index)
            return

        # ── Skip for the expanded row itself (empty-dict pattern) ─────────────
        try:
            col0 = index.model().index(row, 0)
            rd   = col0.data(Qt.UserRole)
            if isinstance(rd, dict) and rd.get("symbol","") == "" and rd.get("sell","") == "":
                return
        except Exception:
            pass

        # ── Hover background (our own — light white overlay on any theme) ─────
        if (
            row == self.table.hovered_row
            and not (option.state & QStyle.State_Selected)
        ):
            painter.fillRect(option.rect, QColor(255, 255, 255, 22))

        # ── For the TIME column on a hovered row: draw star instead ───────────
        try:
            last_col = self.table.model.columnCount() - 1
            is_hovered = (row == self.table.hovered_row)
            if (
                is_hovered
                and col == last_col
                and getattr(self.table, 'show_hover_favorite', True)
            ):
                symbol = None
                try:
                    symbol = self.table.get_symbol_at_row(row)
                except Exception:
                    pass

                # fallback: try UserRole on col 0
                if not symbol:
                    try:
                        col0 = index.model().index(index.row(), 0)
                        rd   = col0.data(Qt.UserRole)
                        if isinstance(rd, dict):
                            symbol = rd.get("symbol")
                    except Exception:
                        pass

                if symbol:
                    is_fav = False
                    try:
                        sm = getattr(self.table, 'symbol_manager', None)
                        if sm:
                            is_fav = sm.is_favorite(symbol)
                    except Exception:
                        pass

                    star  = "★" if is_fav else "☆"
                    color = QColor('#ffc107') if is_fav else QColor('#aaaaaa')

                    painter.save()
                    font = QFont(); font.setPointSize(14)
                    painter.setFont(font)
                    painter.setPen(color)
                    painter.drawText(option.rect, Qt.AlignCenter, star)
                    painter.restore()
                    return   # star replaces time text — skip default paint
        except RuntimeError:
            pass

        # ── Default cell paint ────────────────────────────────────────────────
        super().paint(painter, option, index)