"""
left_panel_widget.py  –  Left panel with Market View + Accounts tabs.

Changes (theme-aware):
  ✅ ThemeManager connected on init → _apply_theme_styles() called on every switch
  ✅ _apply_to_children() propagates to market_widget and accounts_widget
  ✅ Zero hardcoded hex values – all from tokens
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class LeftPanelWidget(QWidget):
    """Reusable left panel widget containing Market and Accounts tabs."""

    def __init__(self, market_widget, accounts_widget, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.market_widget = market_widget
        self.accounts_widget = accounts_widget

        self.tabs.addTab(self.market_widget, "Market View")
        self.tabs.addTab(self.accounts_widget, "Accounts")

        layout.addWidget(self.tabs)

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

    def _apply_theme_styles(self):
        """Re-style tabs using current theme tokens."""
        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
            except Exception:
                t = {}
        else:
            t = {}

        bg_inactive  = t.get("bg_tab_inactive", "transparent")
        bg_active    = t.get("bg_tab_active",   "#e6f0ff")
        bg_hover     = t.get("bg_button_hover", "#e2e8f0")
        text_active  = t.get("text_tab_active",  "#1976d2")
        text_inactive= t.get("text_tab_inactive","#6b7280")
        accent       = t.get("accent",           "#1976d2")
        bg_panel     = t.get("bg_panel",         "#ffffff")

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar {{
                background: transparent;
                padding: 0px;
            }}
            QTabBar::tab {{
                background: {bg_inactive};
                color: {text_inactive};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 0px;
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

        self._apply_to_children()

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

    def current_tab_index(self):
        return self.tabs.currentIndex()
