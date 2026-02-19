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

        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #ccc;
            }
            QListWidget {
                border: none;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()
        self.list.setUniformItemSizes(True)
        # Prevent mouse events from propagating and stealing focus
        self.list.setAttribute(Qt.WA_NoMousePropagation, True)
        # Keep keyboard focus on the search input; list should not take focus
        self.list.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.list)

        self.list.itemClicked.connect(self._on_item_clicked)

    # -------------------------
    # Public API
    # -------------------------
    def show_results(self, results):
        self.list.clear()

        from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

        for sym in results:
            symbol = sym.get("symbol")
            desc = sym.get("name") or sym.get("description", "")
            is_fav = self.symbol_manager.is_favorite(symbol)

            item = QListWidgetItem()
            item.setData(Qt.UserRole, symbol)

            # Create widget for item: label on left, star button on right
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(8, 4, 8, 4)
            h.setSpacing(8)

            lbl = QLabel(f"{symbol} - {desc}" if desc else symbol)
            lbl.setStyleSheet("color: #111; font-size: 14px;")
            star_btn = QPushButton("★" if is_fav else "☆")
            star_btn.setFlat(True)
            star_btn.setStyleSheet(f"color: {'#ffa500' if is_fav else '#999'}; background: transparent; border: none; font-size: 16px;")
            star_btn.setFixedSize(24, 24)
            # Clicking the star should not steal keyboard focus from the search input
            star_btn.setFocusPolicy(Qt.NoFocus)

            # Connect star toggle
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


