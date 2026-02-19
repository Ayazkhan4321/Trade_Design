from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtCore import QTimer

from .order_table import OrderTable
from .orders_empty_state import OrdersEmptyState


class OrdersTab(QWidget):
    def __init__(self, order_service=None):
        super().__init__()

        self.table = OrderTable(order_service=order_service)
        self.empty_state = OrdersEmptyState()

        self.stack = QStackedLayout()
        self.stack.addWidget(self.empty_state)  # index 0
        self.stack.addWidget(self.table)        # index 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)

        layout.addLayout(self.stack)

        model = self.table.model
        model.rowsInserted.connect(self.refresh_view)
        model.rowsRemoved.connect(self.refresh_view)
        model.layoutChanged.connect(self.refresh_view)
        model.dataChanged.connect(self.update_net_pl)

        # run once after show
        QTimer.singleShot(0, self.refresh_view)

    def update_net_pl(self, *args, **kwargs):
        """Compute sum of all orders' `pl` and update the bottom bar display."""
        try:
            total = 0.0
            model = self.table.model
            for o in getattr(model, 'orders', []):
                try:
                    total += float(o.get('pl') or 0.0)
                except Exception:
                    continue
            try:
                self.table.bottom_bar.set_net_pl(total)
            except Exception:
                pass
        except Exception:
            pass

    def refresh_view(self):
        has_rows = self.table.model.rowCount() > 0
        self.stack.setCurrentIndex(1 if has_rows else 0)

        # 🔥 force geometry recalculation
        self.adjustSize()
        self.updateGeometry()
