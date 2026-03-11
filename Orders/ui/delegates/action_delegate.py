"""
action_delegate.py
──────────────────
Place this file at:
    Orders/ui/delegates/action_delegate.py

Requires toast_notifications.py in the SAME folder:
    Orders/ui/delegates/toast_notifications.py
"""

from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui     import QColor
from PySide6.QtCore    import Qt, QEvent, QModelIndex, QTimer

# toast_notifications.py must be in the same delegates/ folder
from .toast_notifications import show_info, show_warn, show_error

import logging
LOG = logging.getLogger(__name__)


# ── Shared row-removal helper (also used by bulk-close) ───────────────────
def _remove_row(model, order_id: str) -> None:
    """Safely remove the row matching order_id from model.orders."""
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


# ── CloseDelegate ─────────────────────────────────────────────────────────
class CloseDelegate(QStyledItemDelegate):
    """
    Renders a red ✕ in every cell of the Actions column.
    Left-clicking fires cancel_order() and shows a pill toast.
    """

    def __init__(self, parent=None, order_service=None):
        super().__init__(parent)
        self.order_service   = order_service
        self._processing_ids = set()

    # ── Paint ✕ / spinner ────────────────────────────────────────────
    def paint(self, painter, option, index):
        painter.save()
        try:
            order_id = index.model().orders[index.row()].get('id')
            if order_id in self._processing_ids:
                painter.setPen(QColor("#94a3b8"))
                painter.drawText(option.rect, Qt.AlignCenter, "···")
            else:
                painter.setPen(QColor("#ef4444"))
                painter.drawText(option.rect, Qt.AlignCenter, "✕")
        except Exception:
            painter.setPen(QColor("#ef4444"))
            painter.drawText(option.rect, Qt.AlignCenter, "✕")
        painter.restore()

    # ── Handle click ─────────────────────────────────────────────────
    def editorEvent(self, event, model, option, index):
        if not (event.type() == QEvent.MouseButtonRelease
                and getattr(event, 'button', lambda: None)() == Qt.LeftButton
                and option.rect.contains(event.pos())):
            return False

        row = index.row()
        try:
            order    = model.orders[row]
            order_id = order.get('id') or order.get('orderId')
        except Exception:
            LOG.exception("Cannot read order at row %s", row)
            return False

        if not order_id:
            LOG.warning("No order_id at row %s", row)
            return False

        if order_id in self._processing_ids:
            return True   # already in-flight

        self._processing_ids.add(order_id)

        # snapshot before async
        sym   = (order.get('symbol') or order.get('Symbol') or '').upper()
        typ   = (order.get('type')   or order.get('orderType') or '').capitalize()
        label = f"{sym} {typ}".strip()
        pw    = self.parent()
        svc   = self.order_service

        def _do_close():
            try:
                if svc:
                    try:
                        ok = svc.cancel_order(order_id)
                    except Exception:
                        LOG.exception("cancel_order raised for id=%s", order_id)
                        show_error(pw, "Error closing order. Please try again.")
                        return

                    if ok:
                        LOG.info("Order %s closed OK", order_id)
                        _remove_row(model, order_id)
                        show_info(pw,
                            f"{label} order closed successfully.".strip()
                            if label else "Order closed successfully.")
                    else:
                        LOG.warning("Server refused close for %s", order_id)
                        show_warn(pw,
                            f"Order {order_id} could not be closed by the server.")
                else:
                    # no service wired (dev/offline) — remove locally
                    _remove_row(model, order_id)
                    show_info(pw,
                        f"{label} order removed.".strip() if label else "Order removed.")

            finally:
                self._processing_ids.discard(order_id)

        QTimer.singleShot(0, _do_close)
        return True