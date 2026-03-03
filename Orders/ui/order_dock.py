from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt

from .top_bar import TopBar
from .order_table import OrderTable


class OrderDock(QDockWidget):
    def __init__(self, parent=None, order_service=None):
        super().__init__("Order Desk", parent)

        self.setAllowedAreas(
            Qt.BottomDockWidgetArea |
            Qt.LeftDockWidgetArea |
            Qt.RightDockWidgetArea
        )

        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )

        container = QWidget()
        # Ensure the container reserves vertical space so docks are not collapsed
        # Use a smaller default so the dock starts compact by default
        try:
            container.setMinimumHeight(120)
        except Exception:
            pass
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Use the centralized OrdersWidget (contains TopBar + stacked content)
        from .main_window import OrdersWidget
        self.orders_widget = OrdersWidget(self, order_service=order_service)

        # try to ensure dock is created in docked (non-floating) state
        try:
            self.setFloating(False)
        except Exception:
            pass

        # Connect to OrdersWidget signals (fall back to TopBar if present)
        try:
            # Connect to OrdersWidget's tabwidget and buttons if available
            # try new tabbar first
            tb = getattr(self.orders_widget, 'tabbar', None)
            if tb is not None:
                try:
                    tb.currentChanged.connect(lambda idx, _tb=tb: self._on_tab_changed(_tb.tabText(idx)))
                except Exception:
                    pass
            else:
                tw = getattr(self.orders_widget, 'tabwidget', None)
                if tw is not None:
                    try:
                        tw.currentChanged.connect(lambda idx, _tw=tw: self._on_tab_changed(_tw.tabText(idx)))
                    except Exception:
                        pass
            # Connect direct button clicks if present (regardless of tabbar/tabwidget)
            sb = getattr(self.orders_widget, 'settings_btn', None)
            if sb is not None:
                try:
                    try:
                        sb.setCursor(Qt.PointingHandCursor)
                    except Exception:
                        pass
                    sb.clicked.connect(self._open_settings)
                except Exception:
                    pass
            fb = getattr(self.orders_widget, 'funnel_btn', None)
            if fb is not None:
                try:
                    fb.clicked.connect(self._open_funnel)
                except Exception:
                    pass

            # Fallback: if a TopBar still exists on the widget, connect it too
            tb = getattr(self.orders_widget, 'top_bar', None)
            if tb is not None:
                try:
                    tb.tab_changed.connect(self._on_tab_changed)
                except Exception:
                    pass
                try:
                    tb.settings_requested.connect(self._open_settings)
                except Exception:
                    pass
                try:
                    tb.funnel_requested.connect(self._open_funnel)
                except Exception:
                    pass
        except Exception:
            pass

        # Add the single OrdersWidget which contains the stacked content
        layout.addWidget(self.orders_widget, 1)

        # Ensure dock itself has a sensible (smaller) minimum so layout reserves space
        try:
            self.setMinimumHeight(120)
            self.setMinimumWidth(300)
        except Exception:
            pass

        self.setWidget(container)

    def _on_tab_changed(self, name: str):
        # Update button visibility based on selected tab
        try:
            self.top_bar.update_buttons(name)
        except Exception:
            pass

    def _open_settings(self):
        # Open settings only when in Order or History
        try:
            # Determine active tab name: prefer OrdersWidget.tabbar, fall back to top_bar.tabbar
            active = None
            try:
                tb = getattr(self.orders_widget, 'tabbar', None)
                if tb is not None:
                    active = tb.tabText(tb.currentIndex())
            except Exception:
                active = None

            if not active:
                try:
                    active = self.top_bar.tabbar.tabText(self.top_bar.tabbar.currentIndex())
                except Exception:
                    active = None

            if active:
                active = active.split('(')[0].strip()

            if active in ("Order", "History"):
                # show the appropriate dialog
                try:
                    from .table_settings import OrderTableSettingsDialog, HistoryTableSettingsDialog
                    if active == "Order":
                        # if we can, provide direct reference to speed lookups
                        try:
                            tv = self.orders_widget.orders_tab.table.table_view
                        except Exception:
                            tv = None
                        dlg = OrderTableSettingsDialog(self, table_view=tv)
                    else:
                        # history dialog will now honour a table_view argument
                        # just as the order dialog does – pass the history view
                        try:
                            # HistoryTable uses attribute `view` instead of `table`.
                            tv = self.orders_widget.history_tab.view
                        except Exception:
                            tv = None
                        dlg = HistoryTableSettingsDialog(self, table_view=tv)
                    dlg.exec()
                except Exception:
                    QMessageBox.information(self, "Settings", f"Open settings for {active}")
        except Exception:
            pass

    def _open_funnel(self):
        # Open funnel only when in History or Logs
        try:
            try:
                active = self.top_bar.tabbar.tabText(self.top_bar.tabbar.currentIndex())
            except Exception:
                active = None

            if active:
                active = active.split('(')[0].strip()

            if active in ("History", "Logs"):
                QMessageBox.information(self, "Filter", f"Open filters for {active}")
        except Exception:
            pass
