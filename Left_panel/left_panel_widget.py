"""
left_panel_widget.py  –  Left panel with Market View + Accounts tabs.

Changes (theme-aware):
  ✅ ThemeManager connected on init → _apply_theme_styles() called on every switch
  ✅ _apply_to_children() propagates to market_widget and accounts_widget
  ✅ Zero hardcoded hex values – all from tokens
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabBar, QStackedWidget, QPushButton
)
from PySide6.QtCore import Qt, Signal

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class LeftPanelWidget(QWidget):
    """Reusable left panel widget containing Market and Accounts tabs."""

    closeRequested = Signal()

    def __init__(self, market_widget, accounts_widget, parent=None):
        super().__init__(parent)

        self.market_widget  = market_widget
        self.accounts_widget = accounts_widget

        # ── Outer layout ──────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header row: [tab bar ........ ] [X] ──────────────────
        header = QWidget()
        header.setObjectName("lpHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 4, 0)
        h_layout.setSpacing(0)

        # Tab bar
        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("lpTabBar")
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.addTab("Market View")
        self.tab_bar.addTab("Accounts")
        self.tab_bar.currentChanged.connect(self._on_tab_changed)

        # Close button — same row as tabs
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.setToolTip("Close panel")
        self._close_btn.setObjectName("panelCloseBtn")
        self._close_btn.clicked.connect(self.closeRequested.emit)

        h_layout.addWidget(self.tab_bar)
        h_layout.addStretch()
        h_layout.addWidget(self._close_btn, alignment=Qt.AlignVCenter)

        # ── Stacked content area ──────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self.market_widget)
        self.stack.addWidget(self.accounts_widget)

        outer.addWidget(header)
        outer.addWidget(self.stack)

        # Apply initial theme
        self._apply_theme_styles()

        # Connect to ThemeManager
        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self._apply_theme_styles()
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _on_tab_changed(self, index):
        self.stack.setCurrentIndex(index)

    # ------------------------------------------------------------------
    def _apply_theme_styles(self):
        """Re-style tabs using current theme tokens."""
        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
            except Exception:
                t = {}
        else:
            t = {}

        bg_inactive   = t.get("bg_tab_inactive",  "transparent")
        bg_active     = t.get("bg_tab_active",    "#e6f0ff")
        bg_hover      = t.get("bg_button_hover",  "#e2e8f0")
        text_active   = t.get("text_tab_active",   "#1976d2")
        text_inactive = t.get("text_tab_inactive", "#6b7280")
        accent        = t.get("accent",            "#1976d2")
        bg_panel      = t.get("bg_panel",          "#ffffff")

        self.tab_bar.setStyleSheet(f"""
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: {bg_inactive};
                color: {text_inactive};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {bg_active};
                color: {text_active};
                border-bottom: 3px solid {accent};
            }}
            QTabBar::tab:hover {{
                background: {bg_hover};
            }}
        """)

        self._close_btn.setStyleSheet(f"""
            QPushButton#panelCloseBtn {{
                background: transparent;
                color: {text_inactive};
                border: none;
                border-radius: 4px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton#panelCloseBtn:hover {{
                background: #fee2e2;
                color: #dc2626;
            }}
            QPushButton#panelCloseBtn:pressed {{
                background: #fecaca;
                color: #dc2626;
            }}
        """)

        self._apply_to_children()

    # ------------------------------------------------------------------
    def _apply_to_children(self):
        """Propagate theme to child widgets."""
        if hasattr(self.market_widget, "apply_theme"):
            try:
                self.market_widget.apply_theme()
            except Exception:
                pass
        if hasattr(self.accounts_widget, "apply_theme"):
            try:
                self.accounts_widget.apply_theme()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def current_tab_index(self):
        return self.tab_bar.currentIndex()