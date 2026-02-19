from PySide6.QtWidgets import QStyledItemDelegate, QMessageBox
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QRect, QEvent, QModelIndex
import logging

LOG = logging.getLogger(__name__)


class CloseDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, order_service=None):
        super().__init__(parent)
        self.order_service = order_service

    def paint(self, painter, option, index):
        painter.save()

        rect = option.rect
        painter.setPen(Qt.red)
        painter.drawText(rect, Qt.AlignCenter, "✕")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        # Only handle left-button mouse releases
        if event.type() == QEvent.MouseButtonRelease and getattr(event, 'button', lambda: None)() == Qt.LeftButton:
            row = index.row()
            LOG.debug("Close order at row %s", row)

            # Try to close via OrderService if available; fall back to local removal
            try:
                order = model.orders[row]
                order_id = order.get('id') or order.get('orderId')
            except Exception:
                LOG.exception("Failed reading order at row %s", row)
                return False

            if self.order_service:
                try:
                    LOG.debug("Calling OrderService.cancel_order for id=%s", order_id)
                    ok = self.order_service.cancel_order(order_id)
                    if ok:
                        LOG.info("Order %s closed successfully, removing row %s", order_id, row)
                        # Show a confirmation message to the user with symbol and type
                        try:
                            sym = order.get('symbol') or order.get('Symbol') or ''
                            typ = order.get('type') or order.get('orderType') or ''
                            title = "Order Closed"
                            body = f"{sym} {typ} order closed"
                            QMessageBox.information(self.parent() or None, title, body)
                        except Exception:
                            LOG.exception("Failed showing order-closed message box for %s", order_id)
                        try:
                            model.beginRemoveRows(QModelIndex(), row, row)
                            model.orders.pop(row)
                            model.endRemoveRows()
                        except Exception:
                            LOG.exception("Failed to remove order row %s after successful close", row)
                        return True
                    else:
                        LOG.warning("OrderService reported failure closing order %s", order_id)
                        return False
                except Exception:
                    LOG.exception("Exception when calling OrderService.cancel_order for %s", order_id)
                    return False

            # No order_service: remove locally (best-effort)
            try:
                model.beginRemoveRows(QModelIndex(), row, row)
                model.orders.pop(row)
                model.endRemoveRows()
            except Exception:
                LOG.exception("Failed to remove order row %s", row)

            return True

        return False
