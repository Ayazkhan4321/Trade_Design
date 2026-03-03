from PySide6.QtWidgets import QStyledItemDelegate, QMessageBox
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QRect, QEvent, QModelIndex, QTimer
import logging

LOG = logging.getLogger(__name__)


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
                                # Show a confirmation message to the user with symbol and type
                                try:
                                    sym = order.get('symbol') or order.get('Symbol') or ''
                                    typ = order.get('type') or order.get('orderType') or ''
                                    title = "Order Closed"
                                    body = f"{sym} {typ} order closed"
                                    QMessageBox.information(self.parent() or None, title, body)
                                except Exception:
                                    LOG.exception("Failed showing order-closed message box for %s", order_id)
                                    
                                for i, o in enumerate(model.orders):
                                    if str(o.get('id') or o.get('orderId')) == str(order_id):
                                        try:
                                            model.beginRemoveRows(QModelIndex(), i, i)
                                            model.orders.pop(i)
                                            model.endRemoveRows()
                                        except Exception:
                                            LOG.exception("Failed to remove order row %s after successful close", i)
                                        break
                                return True
                            else:
                                LOG.warning("OrderService reported failure closing order %s", order_id)
                                QMessageBox.warning(self.parent() or None, "Action Failed", f"Order {order_id} could not be closed by the server.")
                                return False
                        except Exception:
                            LOG.exception("Exception when calling OrderService.cancel_order for %s", order_id)
                            QMessageBox.critical(self.parent() or None, "Error", f"Error closing order.")
                            return False

                    # No order_service: remove locally (best-effort)
                    for i, o in enumerate(model.orders):
                        if str(o.get('id') or o.get('orderId')) == str(order_id):
                            try:
                                model.beginRemoveRows(QModelIndex(), i, i)
                                model.orders.pop(i)
                                model.endRemoveRows()
                            except Exception:
                                LOG.exception("Failed to remove order row %s", i)
                            break

                finally:
                    self._processing_ids.discard(order_id)

            QTimer.singleShot(0, _do_close)
            return True

        return False