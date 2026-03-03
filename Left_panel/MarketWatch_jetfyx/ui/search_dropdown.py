from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class SearchDropdown(QWidget):
    """Popup dropdown for global symbol search"""

    symbolSelected = Signal(str)
    favoriteToggled = Signal(str, bool)

    def __init__(self, symbol_manager, parent=None):
        super().__init__(parent)

        self.symbol_manager = symbol_manager

        # Use a tool window instead of Qt.Popup so it doesn't grab focus
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Do not steal focus when showing popup so typing can continue
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

    def _apply_theme(self):
        """Apply theme-aware styles."""
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            bg     = t.get("bg_popup",      "#ffffff")
            border = t.get("border_primary", "#e5e7eb")
            hover  = t.get("bg_row_hover",   "#f0f4f8")
            text   = t.get("text_primary",   "#1a202c")
        except Exception:
            bg="#ffffff"; border="#ccc"; hover="#f0f0f0"; text="#111"

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QListWidget {{
                border: none;
                background: {bg};
            }}
            QListWidget::item {{
                padding: 6px;
                color: {text};
            }}
            QListWidget::item:hover {{
                background: {hover};
            }}
        """)
        return bg, border, hover, text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()
        self.list.setUniformItemSizes(True)
        self.list.setAttribute(Qt.WA_NoMousePropagation, True)
        self.list.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.list)

        self.list.itemClicked.connect(self._on_item_clicked)

        # Apply theme and subscribe to changes
        self._apply_theme()
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass

    # -------------------------
    # Public API
    # -------------------------
    def show_results(self, results):
        self.list.clear()

        from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

        # Get current theme colors
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            text_color = t.get("text_primary", "#1a202c")
        except Exception:
            text_color = "#111"

        for sym in results:
            symbol = sym.get("symbol")
            desc = sym.get("name") or sym.get("description", "")
            is_fav = self.symbol_manager.is_favorite(symbol)

            item = QListWidgetItem()
            item.setData(Qt.UserRole, symbol)

            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(8, 4, 8, 4)
            h.setSpacing(8)

            lbl = QLabel(f"{symbol} - {desc}" if desc else symbol)
            lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent;")
            star_btn = QPushButton("★" if is_fav else "☆")
            star_btn.setFlat(True)
            star_btn.setStyleSheet(
                f"color: {'#ffa500' if is_fav else '#aaa'}; "
                "background: transparent; border: none; font-size: 16px;"
            )
            star_btn.setFixedSize(24, 24)
            star_btn.setFocusPolicy(Qt.NoFocus)

            def make_toggle(s):
                def _toggle():
                    if self.symbol_manager.is_favorite(s):
                        self.symbol_manager.remove_favorite(s)
                        self.favoriteToggled.emit(s, False)
                    else:
                        self.symbol_manager.add_favorite(s)
                        self.favoriteToggled.emit(s, True)
                return _toggle

            star_btn.clicked.connect(make_toggle(symbol))

            h.addWidget(lbl)
            h.addStretch()
            h.addWidget(star_btn)

            self.list.addItem(item)
            self.list.setItemWidget(item, w)

        if results:
            self.show()
        else:
            self.hide()

    # -------------------------
    # Events
    # -------------------------
    def _on_item_clicked(self, item):
        symbol = item.data(Qt.UserRole)
        if not symbol:
            return

        # Emit selection
        self.symbolSelected.emit(symbol)

    

    def showEvent(self, event):
        super().showEvent(event)
        # Do NOT steal focus from the search input; keep typing working
        pass