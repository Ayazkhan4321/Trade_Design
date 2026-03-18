from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


# ── Token resolution (proven pattern) ────────────────────────────────────────
def _detect_dark() -> bool:
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()
        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool): return val
            s = str(val).lower()
            if s in ("true","1","yes","dark"): return True
            if s in ("false","0","no","light"): return False
        for key in ("bg_panel","background","bg_primary","bg_base","bg"):
            cs = tok.get(key)
            if cs:
                c = QColor(cs)
                if c.isValid(): return c.lightness() < 128
    except Exception: pass
    try:
        app = QApplication.instance()
        if app: return app.palette().window().color().lightness() < 128
    except Exception: pass
    return False


def _resolve() -> dict:
    try:
        from Theme.theme_manager import ThemeManager
        raw = ThemeManager.instance().tokens()
    except Exception:
        raw = {}
    dark = _detect_dark()
    def t(*keys, fd, fl):
        for k in keys:
            v = raw.get(k)
            if v: return v
        return fd if dark else fl
    return {
        "bg":       t("bg_panel","background","bg_primary",       fd="#151e2d", fl="#ffffff"),
        "bg_input": t("bg_input","bg_secondary","bg_surface",      fd="#1e2a3a", fl="#f9fafb"),
        "bg_hover": t("bg_hover","bg_button_hover","bg_row_hover", fd="#1e2d3d", fl="#e8f0fe"),
        "bg_sel":   t("bg_tab_active","bg_selected","selection_bg",fd="#1a3a5c", fl="#dbeafe"),
        "text":     t("text_primary","text","fg",                  fd="#e2e8f0", fl="#111827"),
        "text_sec": t("text_secondary","text_muted",               fd="#94a3b8", fl="#6b7280"),
        "border":   t("border","border_color","border_separator",  fd="#2d3a4a", fl="#e2e8f0"),
        "accent":   t("accent","primary","color_accent",           fd="#3b82f6", fl="#2563eb"),
        "sep":      t("border","border_separator","divider",       fd="#2d3a4a", fl="#f3f4f6"),
    }


class SymbolSearchDialog(QDialog):
    """Frameless symbol search matching reference design."""

    symbolSelected = Signal(str, str, str)  # name, sell, buy

    def __init__(self, symbol_manager, parent=None):
        super().__init__(
            parent,
            Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.symbol_manager = symbol_manager
        self.setFixedSize(420, 320)

        self._build_ui()
        self._apply_theme()
        self.load_symbols()

        if _THEME_AVAILABLE:
            try:
                self._on_theme_cb = lambda n, t: self._apply_theme()
                ThemeManager.instance().theme_changed.connect(self._on_theme_cb)
            except Exception:
                pass

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Card frame
        self._card = QFrame(self)
        self._card.setObjectName("ss_card")
        self._card.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._card)

        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("ss_search")
        self.search_input.setPlaceholderText("Search symbol...")
        self.search_input.setFixedHeight(44)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter)
        card_lay.addWidget(self.search_input)

        # Divider
        div = QFrame(); div.setObjectName("ss_div")
        div.setFrameShape(QFrame.HLine); div.setFixedHeight(1)
        card_lay.addWidget(div)

        # Results list
        self.symbol_list = QListWidget()
        self.symbol_list.setObjectName("ss_list")
        self.symbol_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.symbol_list.setFrameShape(QFrame.NoFrame)
        self.symbol_list.setSpacing(0)
        self.symbol_list.itemClicked.connect(self._on_selected)
        self.symbol_list.itemActivated.connect(self._on_selected)
        card_lay.addWidget(self.symbol_list, 1)

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _apply_theme(self):
        c = _resolve()
        bg       = c["bg"];      bg_input = c["bg_input"]
        bg_hover = c["bg_hover"]; bg_sel   = c["bg_sel"]
        text     = c["text"];    text_sec  = c["text_sec"]
        border   = c["border"];  accent    = c["accent"]
        sep      = c["sep"]

        # Outer transparent
        self.setStyleSheet("SymbolSearchDialog { background: transparent; border: none; }")

        # Card
        self._card.setStyleSheet(
            f"QFrame#ss_card {{ background-color: {bg}; "
            f"border: 1px solid {border}; border-radius: 8px; }}"
        )

        # Search input
        self.search_input.setStyleSheet(f"""
            QLineEdit#ss_search {{
                background-color: {bg_input};
                color: {text};
                border: none;
                border-radius: 0px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 0px 14px;
                font-size: 14px;
            }}
            QLineEdit#ss_search:focus {{
                background-color: {bg_input};
                border-bottom: 2px solid {accent};
            }}
        """)

        # Divider
        div = self._card.findChild(QFrame, "ss_div")
        if div:
            div.setStyleSheet(
                f"QFrame#ss_div {{ background-color: {border}; border: none; "
                f"min-height: 1px; max-height: 1px; }}"
            )

        # List
        self.symbol_list.setStyleSheet(f"""
            QListWidget#ss_list {{
                background-color: {bg};
                color: {text};
                border: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                font-size: 13px;
                outline: 0;
            }}
            QListWidget#ss_list::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {sep};
                color: {text};
                background-color: {bg};
            }}
            QListWidget#ss_list::item:last {{
                border-bottom: none;
            }}
            QListWidget#ss_list::item:hover {{
                background-color: {bg_hover};
                color: {text};
            }}
            QListWidget#ss_list::item:selected {{
                background-color: {bg_sel};
                color: {text};
            }}
            QScrollBar:vertical {{
                background: {bg_input};
                width: 5px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {border};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    # ── Position — open just below the search/dropdown trigger ───────────────
    def showEvent(self, event):
        super().showEvent(event)
        self._position()
        self.search_input.setFocus()

    def _position(self):
        """
        Anchor below the ▾ dropdown button if findable,
        otherwise centre on the parent OrderDialog.
        """
        try:
            p = self.parent()
            if p is None:
                return

            # Try to find the symbol_dropdown button on the parent
            from PySide6.QtWidgets import QPushButton
            btn = getattr(p, 'symbol_dropdown', None)

            if btn is not None and btn.isVisible():
                # Align left edge of popup with left edge of button, open below it
                btn_bl = btn.mapToGlobal(QPoint(0, btn.height()))
                btn_br = btn.mapToGlobal(QPoint(btn.width(), btn.height()))
                # Centre popup under the button area
                x = btn_bl.x() - (self.width() // 2) + (btn.width() // 2)
                y = btn_bl.y() + 6
            else:
                # Fallback: centre on parent dialog
                pg  = p.mapToGlobal(QPoint(0, 0))
                x   = pg.x() + (p.width()  - self.width())  // 2
                y   = pg.y() + 60

            screen = QApplication.screenAt(QPoint(x, y)) or QApplication.primaryScreen()
            avail  = screen.availableGeometry()
            x = max(avail.left() + 4, min(x, avail.right()  - self.width()  - 4))
            y = max(avail.top()  + 4, min(y, avail.bottom() - self.height() - 4))
            self.move(x, y)
        except Exception:
            pass

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_symbols(self):
        self.symbol_list.clear()
        try:
            all_symbols = self.symbol_manager.get_all_symbols()
        except Exception:
            return

        for sd in all_symbols:
            name = sell = buy = ""
            if isinstance(sd, dict):
                name = sd.get('symbol') or sd.get('name') or ""
                sell = str(sd.get('sell', ""))
                buy  = str(sd.get('buy', ""))
            elif isinstance(sd, (list, tuple)) and len(sd) >= 1:
                name = str(sd[0])
                sell = str(sd[1]) if len(sd) > 1 else ""
                buy  = str(sd[2]) if len(sd) > 2 else ""
            if not name:
                continue

            # Show as "SYMBOL  •  sell / buy" if prices available, else just name
            display = f"{name}  •  {sell} / {buy}" if sell else name
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, {"name": name, "sell": sell, "buy": buy})
            self.symbol_list.addItem(item)

    def _filter(self, text: str):
        q = text.upper()
        for i in range(self.symbol_list.count()):
            item = self.symbol_list.item(i)
            d    = item.data(Qt.UserRole)
            item.setHidden(q not in (d.get("name") or "").upper())

    def _on_selected(self, item: QListWidgetItem):
        d = item.data(Qt.UserRole)
        self.symbolSelected.emit(d["name"], d["sell"], d["buy"])
        self.accept()

    def keyPressEvent(self, event):
        # Esc closes, Enter/Return selects highlighted item
        if event.key() in (Qt.Key_Escape,):
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cur = self.symbol_list.currentItem()
            if cur:
                self._on_selected(cur)
        elif event.key() in (Qt.Key_Down, Qt.Key_Up):
            self.symbol_list.setFocus()
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.disconnect(self._on_theme_cb)
        except Exception:
            pass
        super().closeEvent(event)