from PySide6.QtWidgets import QMenu
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QPen, QColor,
                           QAction, QRegion, QPainterPath)
from PySide6.QtCore import Qt, Signal, QByteArray, QRect


# ---------------------------------------------------------------------------
# Theme helpers
# ---------------------------------------------------------------------------

def _theme_tokens() -> dict:
    try:
        from Theme.theme_manager import ThemeManager
        return ThemeManager.instance().tokens()
    except Exception:
        return {}


def _is_dark() -> bool:
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            return app.palette().window().color().lightness() < 128
    except Exception:
        pass
    return True


def _resolve(tokens: dict, key: str, dark_fallback: str, light_fallback: str) -> str:
    v = tokens.get(key, "")
    if v and v not in ("transparent", "none", ""):
        return v
    return dark_fallback if _is_dark() else light_fallback


# ---------------------------------------------------------------------------
# SVG icons
# ---------------------------------------------------------------------------

_SVG_NEW_ORDER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="{g}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="8" x2="12" y2="16"/>
  <line x1="8" y1="12" x2="16" y2="12"/>
</svg>"""

_SVG_CHART = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="{a}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="3 17 9 11 13 15 21 7"/>
  <polyline points="17 7 21 7 21 11"/>
</svg>"""

_SVG_INFO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="{a}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="16" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""

_SVG_REFRESH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="{a}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="23 4 23 10 17 10"/>
  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>"""

_SVG_STAR = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
     fill="{a}" stroke="{a}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02
                   12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
</svg>"""


def _svg_pixmap(svg_str: str, size: int = 18) -> QPixmap:
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return pix


# ---------------------------------------------------------------------------
# SymbolContextMenu
# ---------------------------------------------------------------------------

class SymbolContextMenu(QMenu):
    """
    Right-click context menu for a market symbol row.

    Signals
    -------
    newOrderRequested(str)
    showInChartRequested(str)
    viewSymbolInfoRequested(str)
    refreshPriceRequested(str)
    favoriteToggleRequested(str, bool)
    """

    newOrderRequested       = Signal(str)
    showInChartRequested    = Signal(str)
    viewSymbolInfoRequested = Signal(str)
    refreshPriceRequested   = Signal(str)
    favoriteToggleRequested = Signal(str, bool)

    _RADIUS = 10

    def __init__(self, symbol: str, is_favorite: bool = False, parent=None):
        super().__init__(parent)
        self.symbol      = symbol
        self.is_favorite = is_favorite

        self.setWindowFlags(
            self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._build_style()
        self._build_actions()

    # ------------------------------------------------------------------
    # Theme stylesheet
    # ------------------------------------------------------------------

    def _build_style(self):
        tok = _theme_tokens()

        bg      = _resolve(tok, "bg_panel",      "#1e2535", "#ffffff")
        border  = _resolve(tok, "border_subtle",  "#3a4a65", "#c8d4e0")
        text    = _resolve(tok, "text_primary",   "#d1d9e8", "#1a2535")
        hov     = _resolve(tok, "bg_row_hover",   "#2a3550", "#e8f0fb")
        press   = _resolve(tok, "bg_selected",    "#334166", "#c5d8ef")
        sel_txt = _resolve(tok, "text_primary",   "#ffffff",  "#0a1525")
        sep     = _resolve(tok, "border_subtle",  "#2e3a50", "#d0dae8")

        self._bg_color     = QColor(bg)
        self._border_color = QColor(border)

        # The stylesheet handles items/separators only.
        # Background + rounded corners are handled in paintEvent.
        self.setStyleSheet(f"""
            QMenu {{
                background-color: transparent;
                border: none;
                padding: 8px 4px;
            }}
            QMenu::item {{
                color: {text};
                font-size: 13px;
                font-weight: 500;
                padding: 10px 20px 10px 14px;
                border-radius: 6px;
                margin: 1px 5px;
                min-width: 215px;
            }}
            QMenu::item:selected {{
                background-color: {hov};
                color: {sel_txt};
            }}
            QMenu::item:pressed {{
                background-color: {press};
            }}
            QMenu::separator {{
                height: 1px;
                background: {sep};
                margin: 5px 12px;
            }}
            QMenu::icon {{
                padding-left: 6px;
            }}
        """)

        self._ac = _resolve(tok, "accent_blue", "#60a5fa", "#2563eb")
        self._ag = _resolve(tok, "color_buy",   "#22c55e", "#16a34a")

    # ------------------------------------------------------------------
    # paintEvent — draw solid rounded background + theme border
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        r = self._RADIUS
        rect = self.rect()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Clip the entire widget to the rounded shape so items are clipped too
        clip = QPainterPath()
        clip.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), r, r)
        painter.setClipPath(clip)

        # 2. Fill background
        painter.fillPath(clip, self._bg_color)

        # 3. Draw items (Qt paints text, icons, separators, hover)
        painter.setClipping(False)
        super().paintEvent(event)

        # 4. Re-apply clip and draw the border ring on top of everything
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipping(False)
        pen = QPen(self._border_color, 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # Inset by 0.5px so the stroke falls inside the widget bounds
        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, rect.width() - 1, rect.height() - 1, r, r)
        painter.drawPath(path)

        painter.end()

    # ------------------------------------------------------------------
    # Mask — ensures OS-level corners are transparent (no white squares)
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        r  = self._RADIUS
        sz = self.size()
        path = QPainterPath()
        path.addRoundedRect(0, 0, sz.width(), sz.height(), r, r)
        # Convert path to region for the window mask
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _build_actions(self):
        ac, ag = self._ac, self._ag

        a = QAction(QIcon(_svg_pixmap(_SVG_NEW_ORDER.format(g=ag))), "New Order", self)
        a.triggered.connect(lambda: self.newOrderRequested.emit(self.symbol))
        self.addAction(a)

        self.addSeparator()

        a = QAction(QIcon(_svg_pixmap(_SVG_CHART.format(a=ac))), "Show in Chart", self)
        a.triggered.connect(lambda: self.showInChartRequested.emit(self.symbol))
        self.addAction(a)

        a = QAction(QIcon(_svg_pixmap(_SVG_INFO.format(a=ac))), "View Symbol Info", self)
        a.triggered.connect(lambda: self.viewSymbolInfoRequested.emit(self.symbol))
        self.addAction(a)

        self.addSeparator()

        a = QAction(QIcon(_svg_pixmap(_SVG_REFRESH.format(a=ac))), "Refresh Price", self)
        a.triggered.connect(lambda: self.refreshPriceRequested.emit(self.symbol))
        self.addAction(a)

        fav_label = "Remove from Favourites" if self.is_favorite else "Add to Favourites"
        a = QAction(QIcon(_svg_pixmap(_SVG_STAR.format(a=ac))), fav_label, self)
        a.triggered.connect(
            lambda: self.favoriteToggleRequested.emit(self.symbol, not self.is_favorite)
        )
        self.addAction(a)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def show_for_symbol(
        symbol: str,
        is_favorite: bool,
        global_pos,
        parent=None,
        *,
        on_new_order=None,
        on_show_chart=None,
        on_symbol_info=None,
        on_refresh=None,
        on_favorite=None,
    ) -> "SymbolContextMenu":
        menu = SymbolContextMenu(symbol, is_favorite, parent)

        if on_new_order:
            menu.newOrderRequested.connect(on_new_order)
        if on_show_chart:
            menu.showInChartRequested.connect(on_show_chart)
        if on_symbol_info:
            menu.viewSymbolInfoRequested.connect(on_symbol_info)
        if on_refresh:
            menu.refreshPriceRequested.connect(on_refresh)
        if on_favorite:
            menu.favoriteToggleRequested.connect(on_favorite)

        menu.exec(global_pos)
        return menu