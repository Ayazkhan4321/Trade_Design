from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt


class LeftPanelWidget(QWidget):
    """Reusable left panel widget containing Market and Accounts tabs.

    This class is a plain QWidget so it can be embedded inside a QDockWidget
    or used as a central widget where appropriate.
    """

    def __init__(self, market_widget, accounts_widget, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Accept widget instances to avoid constructing internals twice
        self.market_widget = market_widget
        self.accounts_widget = accounts_widget

        self.tabs.addTab(self.market_widget, "Market View")
        self.tabs.addTab(self.accounts_widget, "Accounts")

        # Apply custom tab styling to match Favourites/All Symbols tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar {
                background: transparent;
                padding: 0px 0px;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #666;
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 0px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1976d2;
                border-bottom: 3px solid #1976d2;
            }
            QTabBar::tab:hover {
                background: #e8e8e8;
            }
        """)

        layout.addWidget(self.tabs)

    def current_tab_index(self):
        return self.tabs.currentIndex()
