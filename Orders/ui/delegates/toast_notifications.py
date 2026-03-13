"""
toast_notifications.py
──────────────────────
Place at:  Orders/ui/delegates/toast_notifications.py

Features
────────
  • Pill-shaped toast matching JetFyX web UI
  • ✕  close button with a circular countdown arc that depletes over the duration
  • Green for success, Red for failure/error
  • Slides in from top, gentle float, slides out on dismiss
"""

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QLinearGradient,
    QFontMetrics, QFont, QCursor, QPen
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSequentialAnimationGroup, QRectF,
    QRect, QModelIndex
)
import logging

LOG = logging.getLogger(__name__)


# ── Kind colours ──────────────────────────────────────────────────────────
_KINDS = {
    "info":    dict(bg_top="#2ecc71", bg_bot="#27ae60", icon="✔"),
    "warning": dict(bg_top="#ff5252", bg_bot="#e53935", icon="⚠"),
    "error":   dict(bg_top="#ff5252", bg_bot="#e53935", icon="⚠"),
}

# Layout constants
_H          = 42    # pill height
_PAD_L      = 14    # left padding
_PAD_R      = 12    # right padding
_ICON_W     = 22    # icon column width
_GAP        = 10    # spacing
_BTN_SIZE   = 24    # close circle diameter
_ARC_PEN    = 2.5   # countdown arc stroke width
_TICK_MS    = 40    # repaint interval for arc (ms)


class _Toast(QWidget):

    def __init__(self, parent: QWidget, kind: str,
                 message: str, duration_ms: int = 4000):

        top = parent.window() if parent else None
        super().__init__(top,
                         Qt.FramelessWindowHint |
                         Qt.Tool |
                         Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        cfg             = _KINDS.get(kind, _KINDS["info"])
        self._cfg       = cfg
        self._top       = top
        self._msg       = message
        self._duration  = duration_ms
        self._elapsed   = 0          # ms elapsed for arc
        self._btn_hot   = False

        self.setFixedHeight(_H)

        # ── Calculate exact width from text ───────────────────────────
        f = QFont()
        f.setPointSize(10)
        f.setWeight(QFont.Medium)
        tw = QFontMetrics(f).horizontalAdvance(message)
        w  = _PAD_L + _ICON_W + _GAP + tw + _GAP + _BTN_SIZE + _PAD_R
        w  = max(w, 280)
        self.setFixedWidth(w)

        # Close button rect
        bx = w - _PAD_R - _BTN_SIZE
        by = (_H - _BTN_SIZE) // 2
        self._btn_rect = QRect(bx, by, _BTN_SIZE, _BTN_SIZE)

        # ── Countdown arc repaint timer ───────────────────────────────
        self._arc_timer = QTimer(self)
        self._arc_timer.setInterval(_TICK_MS)
        self._arc_timer.timeout.connect(self._tick_arc)

        # ── Auto-dismiss timer ────────────────────────────────────────
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._dismiss)

        # Show offscreen first so Qt measures widgets
        self.move(-4000, -4000)
        self.show()
        QTimer.singleShot(0, self._place_and_animate)

    def _tick_arc(self):
        self._elapsed += _TICK_MS
        self.update()

    # ── Positioning & animation ───────────────────────────────────────
    def _place_and_animate(self):
        w = self.width()
        if self._top:
            g = self._top.mapToGlobal(QPoint(0, 0))
            x = g.x() + (self._top.width() - w) // 2
            y = g.y() + 56
        else:
            sg = QApplication.primaryScreen().availableGeometry()
            x  = (sg.width() - w) // 2
            y  = 70
        self.move(x, y)

        self._in_anim = QPropertyAnimation(self, b"pos", self)
        self._in_anim.setDuration(300)
        self._in_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._in_anim.setStartValue(QPoint(x, y - 60))
        self._in_anim.setEndValue  (QPoint(x, y))
        self._in_anim.finished.connect(self._on_shown)
        self._in_anim.start()

    def _on_shown(self):
        self._arc_timer.start()
        self._dismiss_timer.start(self._duration)
        self._start_float()

    def _start_float(self):
        if not self.isVisible():
            return
        ry = self.y()
        up   = QPropertyAnimation(self, b"pos", self)
        down = QPropertyAnimation(self, b"pos", self)
        for a, y0, y1 in ((up, ry, ry - 3), (down, ry - 3, ry)):
            a.setDuration(1000)
            a.setEasingCurve(QEasingCurve.InOutSine)
            a.setStartValue(QPoint(self.x(), y0))
            a.setEndValue  (QPoint(self.x(), y1))
        self._float = QSequentialAnimationGroup(self)
        self._float.addAnimation(up)
        self._float.addAnimation(down)
        self._float.setLoopCount(-1)
        self._float.start()

    def _dismiss(self):
        self._dismiss_timer.stop()
        self._arc_timer.stop()
        if hasattr(self, '_float'):
            self._float.stop()
        out = QPropertyAnimation(self, b"pos", self)
        out.setDuration(220)
        out.setEasingCurve(QEasingCurve.InCubic)
        out.setStartValue(self.pos())
        out.setEndValue  (QPoint(self.x(), self.y() - 60))
        out.finished.connect(self.close)
        out.start()
        self._out_anim = out

    # ── Mouse ─────────────────────────────────────────────────────────
    def mouseMoveEvent(self, e):
        was = self._btn_hot
        self._btn_hot = self._btn_rect.contains(e.pos())
        if was != self._btn_hot:
            self.setCursor(Qt.PointingHandCursor if self._btn_hot else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._btn_rect.contains(e.pos()):
            self._dismiss()

    def leaveEvent(self, e):
        if self._btn_hot:
            self._btn_hot = False
            self.setCursor(Qt.ArrowCursor)
            self.update()

    # ── Paint ─────────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        r   = QRectF(self.rect()).adjusted(0, 0, 0, -1)
        rad = r.height() / 2.0

        # 1. Shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 38))
        p.drawRoundedRect(r.adjusted(2, 4, 2, 3), rad, rad)

        # 2. Pill gradient
        grad = QLinearGradient(r.topLeft(), r.bottomLeft())
        grad.setColorAt(0.0, QColor(self._cfg["bg_top"]))
        grad.setColorAt(1.0, QColor(self._cfg["bg_bot"]))
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)
        p.fillPath(path, grad)

        # 3. Top shine
        p.setBrush(Qt.NoBrush)
        p.setPen(QColor(255, 255, 255, 50))
        shine = QRectF(r.x() + 1, r.y() + 1, r.width() - 2, r.height() * 0.44)
        p.drawRoundedRect(shine, rad - 1, rad - 1)

        # 4. Icon  ✔ / ⚠
        f_icon = QFont()
        f_icon.setPointSize(11)
        f_icon.setBold(True)
        p.setFont(f_icon)
        p.setPen(QColor(255, 255, 255, 225))
        p.drawText(QRect(_PAD_L, 0, _ICON_W, _H),
                   Qt.AlignCenter, self._cfg["icon"])

        # 5. Message
        f_msg = QFont()
        f_msg.setPointSize(10)
        f_msg.setWeight(QFont.Medium)
        p.setFont(f_msg)
        p.setPen(QColor(255, 255, 255, 240))
        tx = _PAD_L + _ICON_W + _GAP
        tw = self.width() - tx - _GAP - _BTN_SIZE - _PAD_R
        p.drawText(QRect(tx, 0, tw, _H),
                   Qt.AlignVCenter | Qt.AlignLeft, self._msg)

        # 6. Close button circle ───────────────────────────────────────
        br    = QRectF(self._btn_rect)
        cx    = br.center().x()
        cy    = br.center().y()

        # background circle
        bg_alpha = 80 if self._btn_hot else 50
        p.setBrush(QColor(0, 0, 0, bg_alpha))
        p.setPen(Qt.NoPen)
        p.drawEllipse(br)

        # ✕ text
        f_x = QFont()
        f_x.setPointSize(9)
        f_x.setBold(True)
        p.setFont(f_x)
        p.setPen(QColor(255, 255, 255, 230))
        p.drawText(br.toRect(), Qt.AlignCenter, "✕")

        # 7. Countdown arc (white ring depleting clockwise from top) ───
        progress = min(self._elapsed / max(self._duration, 1), 1.0)
        remaining = 1.0 - progress          # 1.0 = full, 0.0 = gone

        if remaining > 0:
            margin  = 1.5
            arc_r   = br.adjusted(margin, margin, -margin, -margin)
            span    = int(remaining * 360 * 16)  # Qt uses 1/16 degrees
            start   = 90 * 16                     # start from top

            pen = QPen(QColor(255, 255, 255, 200))
            pen.setWidthF(_ARC_PEN)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(arc_r, start, span)


# ── Public API ────────────────────────────────────────────────────────────

def show_info(parent: QWidget, message: str, duration_ms: int = 4000) -> None:
    """Green pill — success."""
    try:
        _Toast(parent, "info", message, duration_ms).raise_()
    except Exception:
        LOG.exception("show_info failed")

def show_warn(parent: QWidget, message: str, duration_ms: int = 4500) -> None:
    """Red pill — action failed."""
    try:
        _Toast(parent, "warning", message, duration_ms).raise_()
    except Exception:
        LOG.exception("show_warn failed")

def show_error(parent: QWidget, message: str, duration_ms: int = 5000) -> None:
    """Red pill — exception / connection error."""
    try:
        _Toast(parent, "error", message, duration_ms).raise_()
    except Exception:
        LOG.exception("show_error failed")


# ── Legacy helpers ────────────────────────────────────────────────────────
def _info(parent, title="", body="", duration_ms=4000):
    show_info(parent, f"{title}  {body}".strip() if body else title, duration_ms)

def _warn(parent, title="", body="", duration_ms=4500):
    show_warn(parent, f"{title}  {body}".strip() if body else title, duration_ms)

def _err(parent, title="", body="", duration_ms=5000):
    show_error(parent, f"{title}  {body}".strip() if body else title, duration_ms)


# ── Row removal ───────────────────────────────────────────────────────────
def _remove_row(model, order_id: str) -> None:
    str_id = str(order_id)
    for i, o in enumerate(model.orders):
        if str(o.get('id') or o.get('orderId', '')) == str_id:
            try:
                model.beginRemoveRows(QModelIndex(), i, i)
                model.orders.pop(i)
                model.endRemoveRows()
                LOG.debug("Row %s removed for order_id=%s", i, order_id)
            except Exception:
                LOG.exception("Failed removing row %s", i)
            return