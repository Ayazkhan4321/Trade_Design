"""
table_settings.py
=================
Table Settings dialogs for Order and History tabs.

Style: matches LogFilterPopup / HistoryFilterPopup —
  • No coloured accent header background
  • Plain white/dark card with title + ✕ close button
  • Soft red close-button hover
  • Opens ABOVE the ⚙ settings button (bottom-half detection)
  • Direct per-widget theming — beats global app stylesheet
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFrame, QGridLayout,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
)

LOG = logging.getLogger(__name__)

_HERE      = os.path.dirname(os.path.abspath(__file__))
_ORDER_CFG = os.path.join(_HERE, "orders_table_settings.json")
_HIST_CFG  = os.path.join(_HERE, "history_table_settings.json")

_OUTER_PAD = 8   # breathing room so border-radius never clips

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


# ── Token resolution (proven BulkCloseDialog pattern) ────────────────────────
def _detect_dark() -> bool:
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()
        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool): return val
            s = str(val).lower()
            if s in ("true","1","yes","dark"): return True
            if s in ("false","0","no","light"): return False
        for key in ("bg_panel","background","bg_primary","bg_base","bg"):
            cs = tok.get(key)
            if cs:
                c = QColor(cs)
                if c.isValid(): return c.lightness() < 128
    except Exception: pass
    try:
        app = QApplication.instance()
        if app: return app.palette().window().color().lightness() < 128
    except Exception: pass
    return False


def _resolve() -> dict:
    try:
        from Theme.theme_manager import ThemeManager
        raw = ThemeManager.instance().tokens()
    except Exception:
        raw = {}
    dark = _detect_dark()
    def t(*keys, fd, fl):
        for k in keys:
            v = raw.get(k)
            if v: return v
        return fd if dark else fl
    return {
        "bg":       t("bg_panel","background","bg_primary",         fd="#151e2d", fl="#ffffff"),
        "bg_input": t("bg_input","bg_secondary","bg_surface",        fd="#1e2a3a", fl="#f9fafb"),
        "bg_hover": t("bg_hover","bg_button_hover","bg_row_hover",   fd="#1e2d3d", fl="#e2e8f0"),
        "text":     t("text_primary","text","fg",                    fd="#e2e8f0", fl="#111827"),
        "text_sec": t("text_secondary","text_muted",                 fd="#94a3b8", fl="#6b7280"),
        "border":   t("border","border_color","border_separator",    fd="#2d3a4a", fl="#e2e8f0"),
        "accent":   t("accent","primary","color_accent",             fd="#3b82f6", fl="#2563eb"),
    }


def _get_tick_path(color: str = "#ffffff") -> str:
    tmp  = tempfile.gettempdir()
    path = os.path.join(tmp, f"jetfyx_tick_{color.replace('#','')}.png")
    px   = QPixmap(18, 18); px.fill(Qt.transparent)
    p    = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
    pen  = QPen(QColor(color)); pen.setWidth(2)
    pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.drawLine(4, 9, 8, 13); p.drawLine(8, 13, 14, 5); p.end()
    px.save(path, "PNG")
    return path.replace("\\", "/")


def _col_index(tv, name: str) -> Optional[int]:
    try:
        model = tv.model(); n = name.strip().lower(); count = model.columnCount()
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if h == n: return i
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if n in h or h in n: return i
    except Exception as e:
        LOG.debug("_col_index(%r): %s", name, e)
    return None


def _set_visible(order_table_or_tv, header: str, visible: bool) -> None:
    if hasattr(order_table_or_tv, 'toggle_column') and hasattr(order_table_or_tv, 'table_view'):
        tv  = order_table_or_tv.table_view
        idx = _col_index(tv, header)
        if idx is None: LOG.warning("Column not found: %r", header); return
        order_table_or_tv.toggle_column(idx, visible)
    else:
        idx = _col_index(order_table_or_tv, header)
        if idx is None: LOG.warning("Column not found: %r", header); return
        order_table_or_tv.setColumnHidden(idx, not visible)


def _load(path: str, labels: list[str], default: bool) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict): data = {}
    except Exception:
        data = {}
    changed = False
    for lbl in labels:
        if lbl not in data:
            data[lbl] = default; changed = True
    if changed: _save(path, data)
    return data


def _save(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        LOG.exception("Cannot save %s", path)


# ── Base dialog ───────────────────────────────────────────────────────────────
class BaseThemedDialog(QDialog):
    """
    Frameless popup styled like LogFilterPopup:
      • Transparent outer shell + padded card QFrame
      • No coloured header bar — plain title row with ✕ close
      • Opens ABOVE the ⚙ settings button
    """

    def __init__(self, parent=None, title="Table Settings"):
        super().__init__(
            parent,
            Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setModal(True)
        self.setFixedWidth(360)

        self._drag_pos = None

        # Outer layout: padding so border-radius never clips
        outer = QVBoxLayout(self)
        outer.setContentsMargins(_OUTER_PAD, _OUTER_PAD, _OUTER_PAD, _OUTER_PAD)
        outer.setSpacing(0)

        # Card
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self.main_container)

        self._card_layout = QVBoxLayout(self.main_container)
        self._card_layout.setContentsMargins(16, 12, 16, 16)
        self._card_layout.setSpacing(0)

        # Title row (no coloured bg — matches filter popup)
        self.header_widget = self._build_title_row(title)
        self._card_layout.addWidget(self.header_widget)

        # Divider below title
        self._div_title = QFrame()
        self._div_title.setObjectName("TitleDiv")
        self._div_title.setFrameShape(QFrame.HLine)
        self._div_title.setFixedHeight(1)
        self._card_layout.addWidget(self._div_title)
        self._card_layout.addSpacing(10)

        # Content area for subclasses
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self._card_layout.addLayout(self.content_layout)

        self._apply_theme()

        if _THEME_AVAILABLE:
            try:
                self._on_theme_cb = lambda n, t: self._apply_theme()
                ThemeManager.instance().theme_changed.connect(self._on_theme_cb)
            except Exception:
                pass

    def _build_title_row(self, title: str) -> QWidget:
        row = QWidget(); row.setObjectName("HeaderWidget")
        lay = QHBoxLayout(row); lay.setContentsMargins(0, 0, 0, 8); lay.setSpacing(0)

        self._lbl_title = QLabel(title)
        self._lbl_title.setObjectName("HeaderTitle")

        self._btn_close = QPushButton("✕")
        self._btn_close.setObjectName("HeaderCloseBtn")
        self._btn_close.setFixedSize(26, 26)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.reject)

        lay.addWidget(self._lbl_title); lay.addStretch(); lay.addWidget(self._btn_close)
        return row

    # ── Positioning ───────────────────────────────────────────────────────────
    def exec(self):
        self.adjustSize()
        QTimer.singleShot(0, self._position)
        return super().exec()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._position)

    def _position(self):
        """Open ABOVE the ⚙ settings button, right-aligned to it."""
        btn = self._find_settings_btn()
        self.adjustSize(); self.ensurePolished()
        pw = self.width(); ph = max(self.sizeHint().height(), self.height())

        screen = None
        if btn and btn.isVisible():
            screen = QApplication.screenAt(btn.mapToGlobal(QPoint(0, 0)))
        if screen is None:
            screen = QApplication.primaryScreen()
        avail = screen.availableGeometry()

        if btn and btn.isVisible():
            btn_tl = btn.mapToGlobal(QPoint(0, 0))
            btn_tr = btn.mapToGlobal(QPoint(btn.width(), 0))
            btn_br = btn.mapToGlobal(QPoint(btn.width(), btn.height()))

            # Right-align popup to button's right edge
            x = btn_br.x() - pw + _OUTER_PAD

            # Settings button is near bottom of screen (Order Desk) → open above
            scr_mid = avail.top() + avail.height() // 2
            if btn_tl.y() >= scr_mid:
                y = btn_tr.y() - ph - 4
            else:
                y_below = btn_br.y() + 4
                y = y_below if y_below + ph <= avail.bottom() else btn_tr.y() - ph - 4

            x = max(avail.left() + 4, min(x, avail.right()  - pw - 4))
            y = max(avail.top()  + 4, min(y, avail.bottom() - ph - 4))
            self.move(x, y)
        else:
            # Fallback: near mouse cursor
            mp = QCursor.pos()
            self.move(
                max(avail.left() + 4, min(mp.x() - pw - 10, avail.right()  - pw - 4)),
                max(avail.top()  + 4, min(mp.y() - 10,      avail.bottom() - ph - 4)),
            )

    def _find_settings_btn(self) -> Optional[QPushButton]:
        # Walk up parent chain
        p = self.parent()
        while p is not None:
            for attr in ("settings_btn", "funnel_btn"):
                btn = getattr(p, attr, None)
                if btn and isinstance(btn, QPushButton): return btn
            try: p = p.parent()
            except Exception: break
        # Fallback: search all top-level widgets
        for w in QApplication.topLevelWidgets():
            btn = w.findChild(QPushButton, "OrdersSettingsBtn")
            if btn and btn.isVisible(): return btn
        return None

    # ── Theme — direct per-widget styling ─────────────────────────────────────
    def _apply_theme(self):
        c = _resolve()
        bg       = c["bg"];      bg_input = c["bg_input"]
        bg_hover = c["bg_hover"]; text    = c["text"]
        text_sec = c["text_sec"]; border  = c["border"]
        accent   = c["accent"]

        # Outer shell transparent
        self.setStyleSheet(
            "BaseThemedDialog, OrderTableSettingsDialog, HistoryTableSettingsDialog "
            "{ background: transparent; border: none; }"
        )

        # Card
        self.main_container.setStyleSheet(
            f"QFrame#MainContainer {{ background-color: {bg}; "
            f"border: 1px solid {border}; border-radius: 6px; }}"
        )

        # Header row — must be explicitly transparent so it doesn't show grey
        self.header_widget.setStyleSheet(
            f"QWidget#HeaderWidget {{ background: transparent; border: none; }}"
        )

        # Title label
        self._lbl_title.setStyleSheet(
            f"QLabel {{ color: {text}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none; }}"
        )

        # Close button — soft red hover
        self._btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {text_sec}; border: none; "
            f"font-size: 13px; font-weight: 600; border-radius: 4px; padding: 0; }}"
            f"QPushButton:hover {{ background-color: rgba(239,68,68,0.15); color: #ef4444; }}"
            f"QPushButton:pressed {{ background-color: rgba(239,68,68,0.30); color: #ef4444; }}"
        )

        # Divider
        self._div_title.setStyleSheet(
            f"QFrame {{ background-color: {border}; border: none; "
            f"min-height: 1px; max-height: 1px; }}"
        )

        # Checkboxes and section labels (applied on the card so children inherit)
        tick = _get_tick_path("#ffffff")
        self.main_container.setStyleSheet(
            self.main_container.styleSheet() + f"""
            QLabel {{ color: {text}; background: transparent; border: none; }}
            QLabel#SectionTitle {{
                color: {text_sec};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }}
            QCheckBox {{
                font-size: 13px;
                color: {text};
                background: transparent;
                padding: 3px 0px;
            }}
            QCheckBox:hover {{ color: {accent}; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1.5px solid {border};
                border-radius: 4px;
                background-color: {bg_input};
                margin-right: 6px;
            }}
            QCheckBox::indicator:hover {{ border-color: {accent}; }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
                image: url("{tick}");
            }}
            """
        )

    # ── Drag to move ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.header_widget.geometry().contains(event.pos()):
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.disconnect(self._on_theme_cb)
        except Exception: pass
        super().closeEvent(event)


# ── OrderTableSettingsDialog ──────────────────────────────────────────────────
class OrderTableSettingsDialog(BaseThemedDialog):
    """Real-time column show/hide for the Orders table."""

    COLUMNS: list[tuple[str, str, str]] = [
        ("Entry Value",  "Entry Value",  "Entry Value"),
        ("Swap",         "SWAP",         "Swap"),
        ("Market Value", "Market Value", "Market Value"),
        ("Commission",   "Commission",   "Commission"),
        ("P/L in %",     "P/L IN %",     "P/L in %"),
        ("Remarks",      "Remarks",      "Remark"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent, title="Table Settings")
        self._tv = table_view
        self._cfg = _load(
            _ORDER_CFG,
            [key for key, _, _ in self.COLUMNS] + ["Multi-Target SL/TP"],
            default=False,
        )
        self._build()
        self._apply_all()

    def _build(self):
        sec1 = QLabel("VISIBLE OPTIONS"); sec1.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec1)
        self.content_layout.addSpacing(4)

        grid = QGridLayout(); grid.setHorizontalSpacing(16); grid.setVerticalSpacing(4)
        for i, (key, header, display) in enumerate(self.COLUMNS):
            cb = self._make_cb(key, header, display)
            grid.addWidget(cb, i // 2, i % 2)
        self.content_layout.addLayout(grid)

        self.content_layout.addSpacing(10)
        sec2 = QLabel("MASTER FEATURES"); sec2.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec2)
        self.content_layout.addSpacing(4)

        cb_m = QCheckBox("Multi-Target SL/TP")
        cb_m.setChecked(bool(self._cfg.get("Multi-Target SL/TP", False)))
        cb_m.setCursor(Qt.PointingHandCursor)
        cb_m.toggled.connect(lambda checked: self._persist_only("Multi-Target SL/TP", checked))
        self.content_layout.addWidget(cb_m)

    def _make_cb(self, key: str, header: str, display: str) -> QCheckBox:
        cb = QCheckBox(display)
        cb.blockSignals(True); cb.setChecked(bool(self._cfg.get(key, False))); cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        cb.toggled.connect(lambda checked, k=key, hdr=header: self._on_toggle(k, hdr, checked))
        return cb

    def _on_toggle(self, key: str, header: str, checked: bool) -> None:
        self._cfg[key] = checked; _save(_ORDER_CFG, self._cfg)
        obj = self._get_order_table()
        if obj: _set_visible(obj, header, checked)

    def _persist_only(self, key: str, checked: bool) -> None:
        self._cfg[key] = checked; _save(_ORDER_CFG, self._cfg)

    def _get_order_table(self):
        if self._tv is not None:
            if hasattr(self._tv, 'toggle_column'): return self._tv
            p = self._tv.parent()
            while p is not None:
                if hasattr(p, 'toggle_column') and hasattr(p, 'table_view'):
                    self._tv = p; return p
                try: p = p.parent()
                except Exception: break

        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "orders_tab", "table"),
                ("orders_tab", "table"), ("table",),
            ):
                try:
                    obj = p
                    for attr in path: obj = getattr(obj, attr)
                    if obj is not None and hasattr(obj, 'toggle_column'):
                        self._tv = obj; return obj
                except AttributeError: pass
            if hasattr(p, 'toggle_column') and hasattr(p, 'table_view'):
                self._tv = p; return p
            try: p = p.parent()
            except Exception: break
        return self._tv

    def _apply_all(self):
        obj = self._get_order_table()
        if obj is None: return
        for key, header, _ in self.COLUMNS:
            _set_visible(obj, header, bool(self._cfg.get(key, False)))


# ── HistoryTableSettingsDialog ────────────────────────────────────────────────
class HistoryTableSettingsDialog(BaseThemedDialog):
    """Real-time column show/hide for the History table."""

    COLUMNS: list[tuple[str, str, str]] = [
        ("Entry Value",  "Entry Value",  "Entry Value"),
        ("Swap",         "SWAP",         "Swap"),
        ("Closed Value", "Closed Value", "Closed Value"),
        ("Commission",   "Commission",   "Commission"),
        ("P/L in %",     "P/L IN %",     "P/L in %"),
        ("Remark",       "Remark",       "Remark"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent, title="Table Settings")
        self._tv = table_view
        self._cfg = _load(
            _HIST_CFG,
            [key for key, _, _ in self.COLUMNS],
            default=False,
        )
        self._build()
        self._apply_all()

    def _build(self):
        sec1 = QLabel("VISIBLE OPTIONS"); sec1.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec1)
        self.content_layout.addSpacing(4)

        grid = QGridLayout(); grid.setHorizontalSpacing(16); grid.setVerticalSpacing(4)
        for i, (key, header, display) in enumerate(self.COLUMNS):
            cb = self._make_cb(key, header, display)
            grid.addWidget(cb, i // 2, i % 2)
        self.content_layout.addLayout(grid)

    def _make_cb(self, key: str, header: str, display: str) -> QCheckBox:
        cb = QCheckBox(display)
        cb.blockSignals(True); cb.setChecked(bool(self._cfg.get(key, False))); cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        cb.toggled.connect(lambda checked, k=key, hdr=header: self._on_toggle(k, hdr, checked))
        return cb

    def _on_toggle(self, key: str, header: str, checked: bool) -> None:
        self._cfg[key] = checked; _save(_HIST_CFG, self._cfg)
        tv = self._get_tv()
        if tv: _set_visible(tv, header, checked)

    def _get_tv(self):
        if self._tv is not None: return self._tv
        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "history_tab", "view"),
                ("orders_widget", "history_tab", "table_view"),
                ("table", "table_view"),
            ):
                try:
                    obj = p
                    for attr in path: obj = getattr(obj, attr)
                    if obj is not None:
                        self._tv = obj; return obj
                except AttributeError: pass
            try: p = p.parent()
            except Exception: break
        return None

    def _apply_all(self):
        tv = self._get_tv()
        if tv is None: return
        for key, header, _ in self.COLUMNS:
            _set_visible(tv, header, bool(self._cfg.get(key, False)))