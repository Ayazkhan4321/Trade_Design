from PySide6.QtWidgets import (
    QDockWidget, QWidget, QFrame, QVBoxLayout, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt

from .order_table import OrderTable


class OrderDock(QDockWidget):
    def __init__(self, parent=None, order_service=None):
        super().__init__("Order Desk", parent)

        self.setAllowedAreas(
            Qt.BottomDockWidgetArea |
            Qt.LeftDockWidgetArea |
            Qt.RightDockWidgetArea
        )

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        
        self.setStyleSheet("""
            QDockWidget { 
                border: none; 
                margin: 0px; 
                padding: 0px; 
                background: #ffffff; 
            }
        """)
        
        empty_title_bar = QWidget()
        empty_title_bar.setFixedSize(0, 0)
        self.setTitleBarWidget(empty_title_bar)

        # 🟢 FIX: Use QFrame instead of QWidget so it actually renders the white background!
        container = QFrame()
        container.setObjectName("OrderDockContainer")
        container.setStyleSheet("QFrame#OrderDockContainer { background: #ffffff; border: none; margin: 0px; padding: 0px; }")
        
        try:
            container.setMinimumHeight(120)
        except Exception:
            pass
            
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        from .main_window import OrdersWidget
        self.orders_widget = OrdersWidget(self, order_service=order_service)

        try:
            self.setFloating(False)
        except Exception:
            pass

        try:
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

            sb = getattr(self.orders_widget, 'settings_btn', None)
            if sb is not None:
                try:
                    sb.clicked.connect(self._open_settings)
                except Exception:
                    pass
            fb = getattr(self.orders_widget, 'funnel_btn', None)
            if fb is not None:
                try:
                    fb.clicked.connect(self._open_funnel)
                except Exception:
                    pass

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

        layout.addWidget(self.orders_widget, 1)

        try:
            self.setMinimumHeight(120)
            self.setMinimumWidth(300)
        except Exception:
            pass

        self.setWidget(container)

    def _on_tab_changed(self, name: str):
        try:
            self.orders_widget.on_tab_changed(name)
        except Exception:
            pass

    def _open_settings(self):
        try:
            active = None
            try:
                tb = getattr(self.orders_widget, 'tabbar', None)
                if tb is not None:
                    active = tb.tabText(tb.currentIndex())
            except Exception:
                active = None

            if not active:
                try:
                    tb = getattr(self.orders_widget, 'tabbar', None)
                    if tb is not None:
                        active = tb.tabText(tb.currentIndex())
                except Exception:
                    active = None

            if active:
                active = active.split('(')[0].strip()

            if active in ("Order", "History"):
                try:
                    from .table_settings import OrderTableSettingsDialog, HistoryTableSettingsDialog
                    if active == "Order":
                        try:
                            tv = self.orders_widget.orders_tab.table.table_view
                        except Exception:
                            tv = None
                        dlg = OrderTableSettingsDialog(self, table_view=tv)
                    else:
                        try:
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
        try:
            active = None
            try:
                tb = getattr(self.orders_widget, 'tabbar', None)
                if tb is not None:
                    active = tb.tabText(tb.currentIndex())
            except Exception:
                active = None

            if active:
                active = active.split('(')[0].strip()

            if active in ("History", "Logs"):
                QMessageBox.information(self, "Filter", f"Open filters for {active}") 
        except Exception:
            pass