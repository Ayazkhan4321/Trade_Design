from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTabBar
from PySide6.QtCore import Qt, Signal


class TopBar(QWidget):
    tab_changed = Signal(str)
    settings_requested = Signal()
    funnel_requested = Signal()

    def __init__(self):
        super().__init__()
        # Reduce overall topbar height so tabs sit closer to surrounding chrome
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Use a native tab bar for consistent tab behavior
        self.tabbar = QTabBar(self)
        self.tabbar.setDrawBase(False)
        self.tabbar.setElideMode(Qt.ElideRight)
        self.tabbar.setExpanding(False)
        self.tabbar.setTabsClosable(False)
        self.tabbar.setUsesScrollButtons(True)

        # Add tabs in logical order
        self.tabbar.addTab("Order (2)")
        self.tabbar.addTab("History")
        self.tabbar.addTab("Inbox")
        self.tabbar.addTab("Logs")

        # Expose convenience references to maintain compatibility
        self.tabs = [self.tabbar.tabText(i) for i in range(self.tabbar.count())]

        # Style the tab bar to look like pill tabs
        tab_style = """
        QTabBar { background: transparent; }
        QTabBar::tab {
            background: #ffffff;
            border: 1px solid #dbeafe;
            padding: 4px 12px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-height: 28px;
            margin: 0; /* remove gaps between tabs */
            margin-right: -1px; /* collapse adjacent borders */
            border-bottom: 1px solid #dbeafe; /* give a thin divider that can be collapsed */
        }
        QTabBar::tab:selected {
            background: #e6f0ff; /* light blue */
            border-color: #93c5fd;
            font-weight: 600;
            border-bottom-color: transparent; /* visually connect to content below */
            margin-bottom: -6px; /* pull selected tab down to touch content */
        }
        QTabBar::tab:hover { background: #f3f7ff; }
        QTabBar::tab:last { margin-right: 0; }
        """

        # reduce any extra spacing so tabs can sit flush against surrounding widgets
        # Pull the tabbar up slightly and remove bottom spacing so it hugs the title and content
        tab_style += "\nQTabBar { margin-top: -8px; margin-bottom: -6px; }"
        self.tabbar.setStyleSheet(tab_style)
        self.tabbar.setFixedHeight(28)
        self.tabbar.setContentsMargins(0, 0, 0, 0)
        # Emit a normalized tab_changed signal when the current tab changes
        self.tabbar.currentChanged.connect(lambda idx: self.tab_changed.emit(self.tabbar.tabText(idx)))

        layout.addWidget(self.tabbar)
        layout.addStretch()

        # Settings button (gear) — visible by default
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(34, 34)
        self.settings_btn.setStyleSheet("border: none; background: transparent; font-size:16px;")
        layout.addWidget(self.settings_btn)

        # Funnel/filters button (optional)
        self.funnel_btn = QPushButton("⏷")
        self.funnel_btn.setCursor(Qt.PointingHandCursor)
        self.funnel_btn.setToolTip("Filter")
        self.funnel_btn.setFixedSize(34, 34)
        self.funnel_btn.setStyleSheet("border: none; background: transparent; font-size:14px;")
        layout.addWidget(self.funnel_btn)

        # Default active tab → first tab
        try:
            self.tabbar.setCurrentIndex(0)
            # emit initial tab
            self.tab_changed.emit(self.tabbar.tabText(0))
        except Exception:
            pass

        # Wire button clicks to signals
        self.settings_btn.clicked.connect(self.settings_requested)
        self.funnel_btn.clicked.connect(self.funnel_requested)

    def set_active_tab(self, name_or_index):
        """Set active tab by index or by visible tab text (accepts 'Order (2)' or 'Order')."""
        try:
            if isinstance(name_or_index, int):
                idx = name_or_index
            elif isinstance(name_or_index, str):
                # try exact match first, then base name without counts
                texts = [self.tabbar.tabText(i) for i in range(self.tabbar.count())]
                if name_or_index in texts:
                    idx = texts.index(name_or_index)
                else:
                    base = name_or_index.split("(")[0].strip()
                    idx = next((i for i, t in enumerate(texts) if t.split("(")[0].strip() == base), 0)
            else:
                return
            self.tabbar.setCurrentIndex(idx)
        except Exception:
            pass

    def update_buttons(self, tab_name: str):
        # Normalize incoming name (handle 'Order (2)')
        base = tab_name.split("(")[0].strip()
        if base in ("Order", "History"):
            self.settings_btn.show()
        else:
            self.settings_btn.hide()

        if base in ("History", "Logs"):
            self.funnel_btn.show()
        else:
            self.funnel_btn.hide()
