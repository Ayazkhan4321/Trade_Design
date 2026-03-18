import logging
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QFrame, QVBoxLayout, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QRect, QPointF, QTimer
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QPen, QColor, QFont, QPainterPath
)
import math

from .order_table import OrderTable

LOG = logging.getLogger(__name__)


def _icon(size: int, color: str, draw_fn) -> QIcon:
    """Helper: create transparent pixmap, call draw_fn(painter, size, color), return QIcon."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    draw_fn(p, size, QColor(color))
    p.end()
    return QIcon(px)


def _make_order_icon(size: int, color: str) -> QIcon:
    """Two vertical arrows side-by-side (↕ style) — up on left, down on right."""
    def draw(p, s, c):
        pen = QPen(c)
        pen.setWidthF(s * 0.10)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx = s / 2.0
        margin = s * 0.18
        top    = s * 0.12
        bot    = s * 0.88
        tip    = s * 0.22   # arrowhead size

        # Left arrow — pointing UP
        lx = cx - s * 0.18
        p.drawLine(QPointF(lx, bot), QPointF(lx, top))
        p.drawLine(QPointF(lx, top), QPointF(lx - tip * 0.7, top + tip))
        p.drawLine(QPointF(lx, top), QPointF(lx + tip * 0.7, top + tip))

        # Right arrow — pointing DOWN
        rx = cx + s * 0.18
        p.drawLine(QPointF(rx, top), QPointF(rx, bot))
        p.drawLine(QPointF(rx, bot), QPointF(rx - tip * 0.7, bot - tip))
        p.drawLine(QPointF(rx, bot), QPointF(rx + tip * 0.7, bot - tip))

    return _icon(size, color, draw)


def _make_history_icon(size: int, color: str) -> QIcon:
    """Clock face — circle with minute (up) and hour (left) hands."""
    def draw(p, s, c):
        pen = QPen(c)
        pen.setWidthF(s * 0.10)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        cx, cy = s / 2.0, s / 2.0
        r = s * 0.42
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r * 0.65))
        p.drawLine(QPointF(cx, cy), QPointF(cx - r * 0.50, cy))

    return _icon(size, color, draw)


def _make_inbox_icon(size: int, color: str) -> QIcon:
    """Envelope — rectangle body with a V-fold on top."""
    def draw(p, s, c):
        pen = QPen(c)
        pen.setWidthF(s * 0.10)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        l = s * 0.12
        r = s * 0.88
        t = s * 0.22
        b = s * 0.78
        mx = s / 2.0

        # Envelope body rectangle
        p.drawLine(QPointF(l, t), QPointF(r, t))
        p.drawLine(QPointF(r, t), QPointF(r, b))
        p.drawLine(QPointF(r, b), QPointF(l, b))
        p.drawLine(QPointF(l, b), QPointF(l, t))
        # V-fold from top-left → centre-mid → top-right
        fold_y = t + (b - t) * 0.42
        p.drawLine(QPointF(l, t), QPointF(mx, fold_y))
        p.drawLine(QPointF(mx, fold_y), QPointF(r, t))

    return _icon(size, color, draw)


def _make_logs_icon(size: int, color: str) -> QIcon:
    """Document with three horizontal lines inside."""
    def draw(p, s, c):
        pen = QPen(c)
        pen.setWidthF(s * 0.10)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        l = s * 0.18
        r = s * 0.82
        t = s * 0.10
        b = s * 0.90

        # Outer rectangle
        p.drawLine(QPointF(l, t), QPointF(r, t))
        p.drawLine(QPointF(r, t), QPointF(r, b))
        p.drawLine(QPointF(r, b), QPointF(l, b))
        p.drawLine(QPointF(l, b), QPointF(l, t))

        # Three horizontal lines inside
        il = l + s * 0.12
        ir = r - s * 0.12
        for frac in (0.35, 0.55, 0.72):
            y = t + (b - t) * frac
            p.drawLine(QPointF(il, y), QPointF(ir, y))

    return _icon(size, color, draw)


_ICON_MAKERS = {
    "Order":   _make_order_icon,
    "History": _make_history_icon,
    "Inbox":   _make_inbox_icon,
    "Logs":    _make_logs_icon,
}


class OrderDock(QDockWidget):
    def __init__(self, parent=None, order_service=None):
        super().__init__("Order Desk", parent)

        self.setAllowedAreas(
            Qt.BottomDockWidgetArea |
            Qt.LeftDockWidgetArea  |
            Qt.RightDockWidgetArea
        )
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setStyleSheet(
            "QDockWidget { border: none; margin: 0px; padding: 0px; background: #ffffff; }"
        )

        empty_title_bar = QWidget()
        empty_title_bar.setFixedSize(0, 0)
        self.setTitleBarWidget(empty_title_bar)

        container = QFrame()
        container.setObjectName("OrderDockContainer")
        container.setStyleSheet(
            "QFrame#OrderDockContainer { background: #ffffff; border: none; margin: 0px; padding: 0px; }"
        )
        container.setMinimumHeight(120)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Load OrdersWidget ────────────────────────────────────────────
        try:
            from .main_window import OrdersWidget
            self.orders_widget = OrdersWidget(self, order_service=order_service)
        except Exception:
            LOG.exception("Failed to create OrdersWidget")
            self.orders_widget = None

        self.setFloating(False)

        if self.orders_widget is not None:
            self._wire_signals()
            self._apply_tab_icons()
            layout.addWidget(self.orders_widget, 1)

            # Re-draw all icons when theme switches (dark↔light color change)
            try:
                from Theme.theme_manager import ThemeManager
                ThemeManager.instance().theme_changed.connect(
                    lambda name, tok: self._apply_tab_icons()
                )
            except Exception:
                pass
        else:
            # Show a visible placeholder so the dock at least renders
            from PySide6.QtWidgets import QLabel
            placeholder = QLabel("Order Desk failed to load — check logs.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #EF4444; font-size: 13px;")
            layout.addWidget(placeholder, 1)

        self.setMinimumHeight(120)
        self.setMinimumWidth(300)
        self.setWidget(container)

    # ── Wire tab/settings/funnel signals ─────────────────────────────────
    def _wire_signals(self):
        ow = self.orders_widget

        # Tab bar — try tabbar attribute first, then tabwidget
        tabbar = getattr(ow, 'tabbar', None)
        tabwidget = getattr(ow, 'tabwidget', None)
        top_bar = getattr(ow, 'top_bar', None)

        if tabbar is not None:
            try:
                tabbar.currentChanged.connect(
                    lambda idx: self._on_tab_changed(self._base_name(tabbar.tabText(idx)))
                )
            except Exception:
                LOG.debug("tabbar.currentChanged connect failed", exc_info=True)
        elif tabwidget is not None:
            try:
                tabwidget.currentChanged.connect(
                    lambda idx: self._on_tab_changed(self._base_name(tabwidget.tabText(idx)))
                )
            except Exception:
                LOG.debug("tabwidget.currentChanged connect failed", exc_info=True)

        if top_bar is not None:
            for sig, slot in (
                ('tab_changed',        lambda n: self._on_tab_changed(self._base_name(n))),
                ('settings_requested', self._open_settings),
                ('funnel_requested',   self._open_funnel),
            ):
                try:
                    getattr(top_bar, sig).connect(slot)
                except Exception:
                    LOG.debug("top_bar.%s connect failed", sig, exc_info=True)

        settings_btn = getattr(ow, 'settings_btn', None)
        if settings_btn is not None:
            try:
                settings_btn.clicked.connect(self._open_settings)
            except Exception:
                LOG.debug("settings_btn connect failed", exc_info=True)

        funnel_btn = getattr(ow, 'funnel_btn', None)
        if funnel_btn is not None:
            try:
                funnel_btn.clicked.connect(self._open_funnel)
            except Exception:
                LOG.debug("funnel_btn connect failed", exc_info=True)

        # Re-apply icons whenever tab text changes (e.g. count updates from "(3)"→"(4)")
        tabbar_ref = getattr(ow, 'tabbar', None) or (
            getattr(ow, 'tabwidget').tabBar()
            if getattr(ow, 'tabwidget', None) else None
        )
        if tabbar_ref is not None:
            try:
                tabbar_ref.currentChanged.connect(
                    lambda idx: self._refresh_tab_icon(tabbar_ref, idx, tabbar_ref.tabText(idx))
                )
            except Exception:
                LOG.debug("tabTextChanged connect failed", exc_info=True)

        # ── Hook order model row changes → update "Order (N)" count ──────
        try:
            order_table = ow.orders_tab.table          # OrderTable widget
            model       = order_table.model
            model.rowsInserted.connect( lambda *_: self._update_order_count())
            model.rowsRemoved.connect(  lambda *_: self._update_order_count())
            model.modelReset.connect(           self._update_order_count)
            model.layoutChanged.connect(        self._update_order_count)
            QTimer.singleShot(0, self._update_order_count)  # set initial count
        except Exception:
            LOG.debug("order count hook failed", exc_info=True)

    # ── Order count in tab label ──────────────────────────────────────────
    def _get_tabbar(self):
        ow = self.orders_widget
        tb = getattr(ow, 'tabbar', None)
        if tb: return tb
        tw = getattr(ow, 'tabwidget', None)
        if tw: return tw.tabBar()
        return None

    def _update_order_count(self):
        """Update the Order tab text to show live row count: ' Order (4)'."""
        try:
            count = self.orders_widget.orders_tab.table.model.rowCount()
            target = self._get_tabbar()
            if target is None:
                return
            for i in range(target.count()):
                if self._base_name(target.tabText(i)) == "Order":
                    expected = f" Order ({count})"
                    if target.tabText(i) != expected:
                        target.blockSignals(True)
                        target.setTabText(i, expected)
                        target.blockSignals(False)
                    break
        except Exception:
            LOG.debug("_update_order_count failed", exc_info=True)

    # ── Add icons to tab headers ──────────────────────────────────────────
    def _apply_tab_icons(self):
        ow = self.orders_widget
        tabbar    = getattr(ow, 'tabbar',    None)
        tabwidget = getattr(ow, 'tabwidget', None)

        target = tabbar or (tabwidget.tabBar() if tabwidget else None)
        if target is None:
            return

        # ── Bold font — heading weight, same point size ───────────────────
        from PySide6.QtGui import QFontMetrics
        from PySide6.QtCore import QSize
        font = target.font()
        font.setBold(True)
        font.setWeight(QFont.ExtraBold)
        target.setFont(font)

        # ── Icon size matches cap-height of the bold font ─────────────────
        fm      = QFontMetrics(font)
        cap_h   = fm.capHeight() if hasattr(fm, 'capHeight') else fm.ascent()
        icon_px = max(cap_h, 12)
        target.setIconSize(QSize(icon_px, icon_px))

        # ── Theme colour — use actual tab text colour from palette ─────────
        # This is always correct for both light and dark themes because it
        # reads the same colour Qt uses to render the tab label text itself.
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            # Prefer tab_text token; fall back to text_primary; last resort palette
            color = (tok.get("tab_text")
                     or tok.get("text_primary")
                     or target.palette().windowText().color().name())
        except Exception:
            # Guaranteed fallback: read from Qt palette of the tabbar itself
            color = target.palette().windowText().color().name()

        # Build QIcon for every tab — drawn at 2× for HiDPI crispness
        draw_size = icon_px * 2

        for i in range(target.count()):
            raw   = target.tabText(i)
            base  = self._base_name(raw)
            count = self._count_suffix(raw)

            maker = _ICON_MAKERS.get(base)
            if maker:
                target.setTabIcon(i, maker(draw_size, color))
                target.setTabText(i, f" {base}{count}")

    # ── Helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _base_name(text: str) -> str:
        """Strip count suffix AND icon prefix — returns bare name e.g. 'Order'."""
        name = text.split('(')[0].strip()
        while name and not name[0].isalpha():
            name = name.lstrip(name[0]).strip()
        return name

    @staticmethod
    def _count_suffix(text: str) -> str:
        """Return ' (N)' count suffix from tab text, or '' if none."""
        if '(' in text and ')' in text:
            try:
                part = text[text.index('('):text.rindex(')') + 1]
                return f" {part}"
            except Exception:
                pass
        return ""

    def _current_tab_name(self) -> str:
        """Return bare tab name ('Order', 'History', etc.) for the active tab.
        Reads directly from tabbar/tabwidget — same as original code."""
        ow = self.orders_widget

        # Priority 1: tabbar (the attribute the original code used)
        tabbar = getattr(ow, 'tabbar', None)
        if tabbar is not None:
            try:
                return self._base_name(tabbar.tabText(tabbar.currentIndex()))
            except Exception:
                pass

        # Priority 2: tabwidget
        tabwidget = getattr(ow, 'tabwidget', None)
        if tabwidget is not None:
            try:
                return self._base_name(tabwidget.tabText(tabwidget.currentIndex()))
            except Exception:
                pass

        return ""

    # ── Slots ─────────────────────────────────────────────────────────────
    def _refresh_tab_icon(self, tabbar, idx: int, new_text: str):
        """Re-apply icon+count after OrdersWidget updates tab text with new count."""
        try:
            base  = self._base_name(new_text)
            count = self._count_suffix(new_text)
            # Order count is managed exclusively by _update_order_count — skip here
            if base == "Order":
                return
            expected = f" {base}{count}"
            if base in _ICON_MAKERS and new_text != expected:
                tabbar.blockSignals(True)
                tabbar.setTabText(idx, expected)
                tabbar.blockSignals(False)
        except Exception:
            LOG.debug("_refresh_tab_icon failed", exc_info=True)

    def _on_tab_changed(self, name: str):
        try:
            clean = self._base_name(name)
            self.orders_widget.on_tab_changed(clean)
        except Exception:
            LOG.debug("on_tab_changed(%r) failed", name, exc_info=True)

    def _open_settings(self):
        try:
            active = self._current_tab_name()
            LOG.debug("_open_settings: active tab = %r", active)

            if active not in ("Order", "History"):
                LOG.debug("Settings not available for tab %r", active)
                return

            from .table_settings import OrderTableSettingsDialog, HistoryTableSettingsDialog

            if active == "Order":
                tv = None
                for path in (
                    ('orders_tab', 'table', 'table_view'),
                    ('orders_tab', 'table'),
                    ('orders_tab',),
                ):
                    try:
                        obj = self.orders_widget
                        for attr in path:
                            obj = getattr(obj, attr)
                        if obj is not None:
                            tv = obj
                            break
                    except AttributeError:
                        pass
                dlg = OrderTableSettingsDialog(self, table_view=tv)
            else:
                tv = None
                for path in (
                    ('history_tab', 'view'),
                    ('history_tab', 'table_view'),
                    ('history_tab',),
                ):
                    try:
                        obj = self.orders_widget
                        for attr in path:
                            obj = getattr(obj, attr)
                        if obj is not None:
                            tv = obj
                            break
                    except AttributeError:
                        pass
                dlg = HistoryTableSettingsDialog(self, table_view=tv)

            dlg.exec()

        except Exception:
            LOG.exception("_open_settings failed")
            QMessageBox.warning(self, "Settings Error",
                                "Could not open table settings.\nCheck the application logs.")

    def _open_funnel(self):
        try:
            active = self._current_tab_name()
            if active not in ("Logs", "History"):
                return

            try:
                from .logs_filter_popup import LogFilterPopup, HistoryFilterPopup
            except ImportError:
                from Orders.ui.logs_filter_popup import LogFilterPopup, HistoryFilterPopup

            ow     = getattr(self, 'orders_widget', None)
            anchor = getattr(ow, 'funnel_btn', None) if ow else None

            if active == "Logs":
                # ── Lazy-create Logs popup ────────────────────────────────
                if not hasattr(self, '_log_filter_popup') or self._log_filter_popup is None:
                    self._log_filter_popup = LogFilterPopup(parent=self)
                    self._log_filter_popup.filters_applied.connect(self._on_log_filters_applied)
                    self._log_filter_popup.filters_cleared.connect(self._on_log_filters_cleared)
                popup = self._log_filter_popup

            else:  # History
                # ── Lazy-create History popup ─────────────────────────────
                if not hasattr(self, '_history_filter_popup') or self._history_filter_popup is None:
                    self._history_filter_popup = HistoryFilterPopup(parent=self)
                    self._history_filter_popup.filters_applied.connect(self._on_history_filters_applied)
                    self._history_filter_popup.filters_cleared.connect(self._on_history_filters_cleared)
                popup = self._history_filter_popup

            # Toggle
            if popup.isVisible():
                popup.hide()
                return

            if anchor is not None:
                popup.show_near(anchor)
            else:
                popup.adjustSize()
                geo = self.geometry()
                popup.move(
                    geo.x() + (geo.width()  - popup.width())  // 2,
                    geo.y() + (geo.height() - popup.height()) // 2,
                )
                popup.show()

        except Exception:
            LOG.debug("_open_funnel failed", exc_info=True)

    def _on_log_filters_applied(self, filters: dict):
        """Called when the user clicks Apply Filters in the log filter popup."""
        try:
            from_date = filters.get("from_date")
            to_date   = filters.get("to_date")
            LOG.info("Log filters applied: from=%s to=%s", from_date, to_date)
            ow = getattr(self, 'orders_widget', None)
            logs_tab = getattr(ow, 'logs_tab', None) if ow else None
            if logs_tab is not None and hasattr(logs_tab, 'apply_date_filter'):
                logs_tab.apply_date_filter(from_date, to_date)
        except Exception:
            LOG.debug("_on_log_filters_applied failed", exc_info=True)

    def _on_log_filters_cleared(self):
        """Called when the user clicks Clear All in the log filter popup."""
        try:
            LOG.info("Log filters cleared")
            ow = getattr(self, 'orders_widget', None)
            logs_tab = getattr(ow, 'logs_tab', None) if ow else None
            if logs_tab is not None and hasattr(logs_tab, 'clear_filter'):
                logs_tab.clear_filter()
        except Exception:
            LOG.debug("_on_log_filters_cleared failed", exc_info=True)

    def _on_history_filters_applied(self, filters: dict):
        """Called when the user clicks Apply Filters in the history filter popup."""
        try:
            from_date = filters.get("from_date")
            to_date   = filters.get("to_date")
            ftype     = filters.get("type", "All")
            LOG.info("History filters applied: from=%s to=%s type=%s", from_date, to_date, ftype)
            ow = getattr(self, 'orders_widget', None)
            history_tab = getattr(ow, 'history_tab', None) if ow else None
            if history_tab is not None and hasattr(history_tab, 'apply_filter'):
                history_tab.apply_filter(from_date, to_date, ftype)
        except Exception:
            LOG.debug("_on_history_filters_applied failed", exc_info=True)

    def _on_history_filters_cleared(self):
        """Called when the user clicks Clear All in the history filter popup."""
        try:
            LOG.info("History filters cleared")
            ow = getattr(self, 'orders_widget', None)
            history_tab = getattr(ow, 'history_tab', None) if ow else None
            if history_tab is not None and hasattr(history_tab, 'clear_filter'):
                history_tab.clear_filter()
        except Exception:
            LOG.debug("_on_history_filters_cleared failed", exc_info=True)