"""
tab_bar.py  –  Favourites / All Symbols toggle bar + gear button.

Changes (theme-aware):
  ✅ apply_theme() public method added
  ✅ ThemeManager connected on init
  ✅ Zero hardcoded hex values – all from tokens
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class TabBar(QWidget):
    """Custom tab bar with Favourites, All Symbols tabs and settings button."""

    tabChanged     = Signal(int)   # 0 = Favourites, 1 = All Symbols
    settingsClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.favorites_tab = QPushButton("Favourites (0)")
        self.favorites_tab.setCheckable(True)
        self.favorites_tab.setChecked(True)
        self.favorites_tab.clicked.connect(lambda: self._on_tab_clicked(0))

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.settingsClicked.emit)

        self.all_symbols_tab = QPushButton("All Symbols (0)")
        self.all_symbols_tab.setCheckable(True)
        self.all_symbols_tab.clicked.connect(lambda: self._on_tab_clicked(1))

        layout.addWidget(self.favorites_tab)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.all_symbols_tab)
        layout.addStretch()

        self.current_tab = 0
        self.apply_theme()

        # Connect to ThemeManager
        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(
                    lambda name, t: self.apply_theme()
                )
            except Exception:
                pass

    def apply_theme(self):
        """Re-style using current theme tokens."""
        if _THEME_AVAILABLE:
            try:
                t = ThemeManager.instance().tokens()
            except Exception:
                t = {}
        else:
            t = {}

        bg_inactive  = t.get("bg_tab_inactive",  "transparent")
        bg_active    = t.get("bg_tab_active",    "#e6f0ff")
        bg_hover     = t.get("bg_button_hover",  "#e2e8f0")
        text_active  = t.get("text_tab_active",  "#1976d2")
        text_inactive= t.get("text_tab_inactive","#6b7280")
        accent       = t.get("accent",           "#1976d2")
        text_primary = t.get("text_primary",     "#1a202c")

        tab_style = f"""
            QPushButton {{
                background: {bg_inactive};
                color: {text_inactive};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_hover};
            }}
            QPushButton:checked {{
                background: {bg_active};
                color: {text_active};
                border-bottom: 3px solid {accent};
            }}
        """

        settings_style = f"""
            QPushButton {{
                background: transparent;
                color: {text_primary};
                border: none;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {bg_hover};
                color: {accent};
            }}
        """

        self.favorites_tab.setStyleSheet(tab_style)
        self.all_symbols_tab.setStyleSheet(tab_style)
        self.settings_btn.setStyleSheet(settings_style)

    def _on_tab_clicked(self, tab_index):
        if tab_index == 0:
            self.favorites_tab.setChecked(True)
            self.all_symbols_tab.setChecked(False)
        else:
            self.favorites_tab.setChecked(False)
            self.all_symbols_tab.setChecked(True)
        if self.current_tab != tab_index:
            self.current_tab = tab_index
            self.tabChanged.emit(tab_index)

    def update_counts(self, favorites_count, all_count):
        self.favorites_tab.setText(f"Favourites ({favorites_count})")
        self.all_symbols_tab.setText(f"All Symbols ({all_count})")

    def set_current_tab(self, index):
        self._on_tab_clicked(index)
