from PySide6.QtWidgets import QStyledItemDelegate, QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QEvent, QModelIndex, QTimer, QPropertyAnimation, QEasingCurve, QPoint
import logging

LOG = logging.getLogger(__name__)


# ── Toast kinds config ────────────────────────────────────────────────────
_KIND = {
    "info":    {"icon": "✔", "bg": "#16a34a", "border": "#22c55e"},
    "warning": {"icon": "⚠", "bg": "#b45309", "border": "#f59e0b"},
    "error":   {"icon": "✕", "bg": "#b91c1c", "border": "#ef4444"},
}


# ── Toast widget ──────────────────────────────────────────────────────────
class _Toast(QWidget):
    def __init__(self, parent: QWidget, kind: str, message: str, duration_ms: int = 3500):
        top = parent.window() if parent else None
        super().__init__(top, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        cfg = _KIND.get(kind, _KIND["info"])
        self._bg     = cfg["bg"]
        self._border = cfg["border"]
        self._top    = top

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 10, 0)
        lay.setSpacing(8)

        icon_lbl = QLabel(cfg["icon"])
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;"
            "background: rgba(255,255,255,0.20); border-radius: 12px;"
        )
        lay.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            "color: white; font-size: 13px; font-weight: 500; background: transparent;"
        )
        msg_lbl.setWordWrap(False)
        lay.addWidget(msg_lbl, 1)

        close_btn = QPushButton("→")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
            "background: rgba(255,255,255,0.18); border-radius: 5px; border: none;"
        )
        close_btn.clicked.connect(self._slide_out)
        lay.addWidget(close_btn)

        self.setFixedHeight(44)
        self.adjustSize()
        self.setMinimumWidth(320)
        self._reposition()

        # Slide-in
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(QPoint(self.x(), self.y() - 60))
        self._anim.setEndValue(QPoint(self.x(), self.y()))
        self.show()
        self._anim.start()

        # Auto-dismiss
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._slide_out)
        self._dismiss_timer.start(duration_ms)

    def _reposition(self):
        if self._top:
            tw = max(self.sizeHint().width(), 380)
            self.setFixedWidth(tw)
            self.move(
                self._top.x() + (self._top.width() - tw) // 2,
                self._top.y() + 60
            )
        else:
            screen = QApplication.primaryScreen().geometry()
            tw = 380
            self.setFixedWidth(tw)
            self.move((screen.width() - tw) // 2, 80)

    def _slide_out(self):
        self._dismiss_timer.stop()
        self._out_anim = QPropertyAnimation(self, b"pos", self)
        self._out_anim.setDuration(220)
        self._out_anim.setEasingCurve(QEasingCurve.InCubic)
        self._out_anim.setStartValue(self.pos())
        self._out_anim.setEndValue(QPoint(self.x(), self.y() - 60))
        self._out_anim.finished.connect(self.close)
        self._out_anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 8, 8)
        p.fillPath(path, QColor(self._bg))
        p.setPen(QColor(self._border))
        p.drawPath(path)


# ── Public toast helpers ──────────────────────────────────────────────────
def _show_toast(parent, kind: str, message: str, duration_ms: int = 3500):
    try:
        _Toast(parent, kind, message, duration_ms).raise_()
    except Exception:
        LOG.exception("Failed to show toast notification")

def _info(parent, title: str, body: str, duration_ms: int = 3500):
    _show_toast(parent, "info", f"{title} — {body}" if title else body, duration_ms)

def _warn(parent, title: str, body: str, duration_ms: int = 3500):
    _show_toast(parent, "warning", f"{title} — {body}" if title else body, duration_ms)

def _err(parent, title: str, body: str, duration_ms: int = 3500):
    _show_toast(parent, "error", f"{title} — {body}" if title else body, duration_ms)


# ── CloseDelegate ─────────────────────────────────────────────────────────
class CloseDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, order_service=None):
        super().__init__(parent)
        self.order_service = order_service
        self._processing_ids = set()

    def paint(self, painter, option, index):
        painter.save()
        rect = option.rect
        try:
            model = index.model()
            order_id = model.orders[index.row()].get('id')
            if order_id in self._processing_ids:
                painter.setPen(Qt.gray)
                painter.drawText(rect, Qt.AlignCenter, "...")
            else:
                painter.setPen(Qt.red)
                painter.drawText(rect, Qt.AlignCenter, "✕")
        except Exception:
            painter.setPen(Qt.red)
            painter.drawText(rect, Qt.AlignCenter, "✕")
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease and \
                getattr(event, 'button', lambda: None)() == Qt.LeftButton:

            row = index.row()
            LOG.debug("Close order at row %s", row)

            try:
                order = model.orders[row]
                order_id = order.get('id') or order.get('orderId')
            except Exception:
                LOG.exception("Failed reading order at row %s", row)
                return False

            if order_id in self._processing_ids:
                return True

            self._processing_ids.add(order_id)

            def _do_close():
                try:
                    if self.order_service:
                        try:
                            LOG.debug("Calling OrderService.cancel_order for id=%s", order_id)
                            ok = self.order_service.cancel_order(order_id)
                            if ok:
                                LOG.info("Order %s closed successfully", order_id)
                                try:
                                    sym = order.get('symbol') or order.get('Symbol') or ''
                                    typ = order.get('type') or order.get('orderType') or ''
                                    _info(self.parent(), "Order Closed",
                                          f"{sym} {typ} order closed successfully")
                                except Exception:
                                    LOG.exception("Failed showing toast for %s", order_id)

                                for i, o in enumerate(model.orders):
                                    if str(o.get('id') or o.get('orderId')) == str(order_id):
                                        try:
                                            model.beginRemoveRows(QModelIndex(), i, i)
                                            model.orders.pop(i)
                                            model.endRemoveRows()
                                        except Exception:
                                            LOG.exception("Failed to remove row %s", i)
                                        break
                                return True
                            else:
                                LOG.warning("OrderService failed closing order %s", order_id)
                                _warn(self.parent(), "Action Failed",
                                      f"Order {order_id} could not be closed.")
                                return False
                        except Exception:
                            LOG.exception("Exception in cancel_order for %s", order_id)
                            _err(self.parent(), "Error", "Error closing order.")
                            return False

                    # No order_service: remove locally
                    for i, o in enumerate(model.orders):
                        if str(o.get('id') or o.get('orderId')) == str(order_id):
                            try:
                                model.beginRemoveRows(QModelIndex(), i, i)
                                model.orders.pop(i)
                                model.endRemoveRows()
                            except Exception:
                                LOG.exception("Failed to remove row %s", i)
                            break

                finally:
                    self._processing_ids.discard(order_id)

            QTimer.singleShot(0, _do_close)
            return True

        return False