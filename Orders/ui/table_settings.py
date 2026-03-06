"""
table_settings.py
=================
Table Settings dialogs for Order and History tabs.
Upgraded with full Dynamic Theming, Emojis, and a Bulletproof PNG File Generator!
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFrame, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget
)

LOG = logging.getLogger(__name__)

_HERE      = os.path.dirname(os.path.abspath(__file__))
_ORDER_CFG = os.path.join(_HERE, "orders_table_settings.json")
_HIST_CFG  = os.path.join(_HERE, "history_table_settings.json")

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_dynamic_tick_path(color_str: str = "#ffffff") -> str:
    tmp_dir = tempfile.gettempdir()
    path = os.path.join(tmp_dir, f"jetfyx_tick_{color_str.replace('#', '')}.png")
    
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(QColor(color_str))
    pen.setWidth(2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    
    painter.drawLine(4, 9, 8, 13)
    painter.drawLine(8, 13, 14, 5)
    painter.end()

    pixmap.save(path, "PNG")
    
    return path.replace("\\", "/")


def _col_index(tv, name: str) -> Optional[int]:
    try:
        model = tv.model()
        n = name.strip().lower()
        count = model.columnCount()
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if h == n: return i
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if n in h or h in n: return i
    except Exception as e:
        LOG.debug("_col_index(%r): %s", name, e)
    return None


def _set_visible(tv, header: str, visible: bool) -> None:
    idx = _col_index(tv, header)
    if idx is None:
        LOG.warning("Column not found: %r", header)
        return
    tv.setColumnHidden(idx, not visible)


def _load(path: str, labels: list[str], default: bool) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    changed = False
    for lbl in labels:
        if lbl not in data:
            data[lbl] = default
            changed = True
    if changed:
        _save(path, data)
    return data


def _save(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        LOG.exception("Cannot save %s", path)


# ─────────────────────────────────────────────────────────────────────────────
# Base Themed Frameless Dialog
# ─────────────────────────────────────────────────────────────────────────────

class BaseThemedDialog(QDialog):
    """Provides a Frameless window styled EXACTLY like the Bulk Close Dialog."""
    def __init__(self, parent=None, title="Table Settings"):
        super().__init__(parent)
        
        # 🟢 FIX: We use standard frameless window to prevent OS interference
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedWidth(380)

        self._drag_pos = None

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_container)

        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(0, 0, 0, 16)
        self.layout.setSpacing(0)

        self.header_widget = self._create_header(title)
        self.layout.addWidget(self.header_widget)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(20, 12, 20, 0)
        self.content_layout.setSpacing(8)
        self.layout.addLayout(self.content_layout)

        self._apply_theme()

        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
            except Exception:
                pass

    # 🟢 THE FIX: Block Qt's auto-centering
    def exec(self):
        self.setAttribute(Qt.WA_Moved, True) # Tell Qt to leave the position alone
        self.adjustSize()
        self._snap_to_button()
        return super().exec()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._snap_to_button)

    def _snap_to_button(self):
        try:
            btn = None
            
            # Find the gear button globally
            for w in QApplication.topLevelWidgets():
                btn = w.findChild(QPushButton, "OrdersSettingsBtn")
                if btn and btn.isVisible():
                    break
                    
            if not btn:
                parent = self.parent()
                if parent and hasattr(parent, 'orders_widget'):
                    btn = getattr(parent.orders_widget, 'settings_btn', None)

            if btn and btn.isVisible():
                btn_pos = btn.mapToGlobal(QPoint(0, 0))
                
                # 🟢 THE FIX: Snap the Right edge of the dialog to the LEFT edge of the button
                x = btn_pos.x() - self.width() - 8
                
                # 🟢 THE FIX: Align the Top edge of the dialog with the Top edge of the button
                y = btn_pos.y()
                
                # Smart screen boundary protection
                screen = QApplication.screenAt(btn_pos)
                if not screen:
                    screen = QApplication.primaryScreen()
                    
                if screen:
                    geom = screen.availableGeometry()
                    # If it clips the bottom of the screen, slide it upwards so it fits perfectly!
                    if (y + self.height()) > geom.bottom():
                        y = geom.bottom() - self.height() - 8
                        
                self.move(x, y)
            else:
                # Failsafe: Open next to the mouse cursor
                mouse_pos = QCursor.pos()
                self.move(mouse_pos.x() - self.width() - 15, mouse_pos.y() - 10)
                
        except Exception as e:
            LOG.debug(f"Failed to position contextual dialog: {e}")

    def _create_header(self, title):
        header = QWidget(self)
        header.setObjectName("HeaderWidget")
        h_layout = QHBoxLayout(header)
        
        h_layout.setContentsMargins(16, 12, 16, 12)
        
        icon = QLabel("⚙️")
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        icon.setFixedWidth(28)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("HeaderTitle")
        
        sub_lbl = QLabel("Customize your table display")
        sub_lbl.setObjectName("HeaderSubtitle")
        
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)
        
        h_layout.addWidget(icon)
        h_layout.addLayout(text_col)
        h_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("HeaderCloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        
        h_layout.addWidget(close_btn)
        return header

    def _apply_theme(self):
        try:
            tok = ThemeManager.instance().tokens()
            bg_panel = tok.get("bg_panel", "#ffffff")
            text_pri = tok.get("text_primary", "#1a202c")
            text_sec = tok.get("text_secondary", "#4a5568")
            border   = tok.get("border_primary", "#e5e7eb")
            bg_input = tok.get("bg_input", "#f5f7fa")
            accent   = tok.get("accent", "#1976d2")
            bg_hover = tok.get("bg_button_hover", "#e2e8f0")
            is_dark  = tok.get("is_dark", "false") == "true"
            acc_t    = "#ffffff" if is_dark else tok.get("accent_text", "#ffffff")
            if "crazy" in ThemeManager.instance().current_theme or not is_dark: acc_t = "#ffffff"
        except Exception:
            bg_panel, text_pri, text_sec, border, accent, bg_input, bg_hover, acc_t, is_dark = (
                "#ffffff", "#1a202c", "#4a5568", "#e5e7eb", "#1976d2", "#f5f7fa", "#e2e8f0", "#ffffff", False
            )

        if is_dark:
            if border == "#e5e7eb": border = "#374151"
            if bg_input == "#f5f7fa": bg_input = "#1f2937"
            if bg_hover == "#e2e8f0": bg_hover = "#2d3748"

        tick_path = _get_dynamic_tick_path("#ffffff")

        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            
            QFrame#MainContainer {{
                background-color: {bg_panel};
                border: 2px solid {accent};
                border-radius: 8px;
            }}
            
            QWidget#HeaderWidget {{
                background-color: {accent};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            
            QLabel#HeaderTitle {{
                color: {acc_t};
                font-size: 16px;
                font-weight: 700;
                background: transparent;
            }}
            
            QLabel#HeaderSubtitle {{
                color: {acc_t};
                font-size: 12px;
                background: transparent;
                opacity: 0.85;
            }}
            
            QPushButton#HeaderCloseBtn {{
                background-color: rgba(255,255,255,0.22);
                border: 2px solid #ffffff;
                border-radius: 5px;
                color: #ffffff;
                font-family: "Segoe UI Symbol", Arial, sans-serif;
                font-size: 14px; 
                font-weight: 900;
                padding: 0px; 
                margin: 0px;
            }}
            
            QPushButton#HeaderCloseBtn:hover {{
                background-color: rgba(210,40,40,0.88);
                border-color: #ffffff;
            }}
            
            QLabel {{ color: {text_pri}; }}
            
            QLabel#SectionTitle {{
                color: {text_sec};
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
                margin-top: 10px;
                text-transform: uppercase;
            }}
            
            QCheckBox {{
                font-size: 13px;
                color: {text_pri};
                background: transparent;
                padding: 4px 0px;
            }}
            
            QCheckBox:hover {{
                color: {accent};
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1.5px solid {border};
                border-radius: 4px;
                background-color: {bg_input};
                margin-right: 8px;
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {accent};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
                image: url("{tick_path}");
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.header_widget.geometry().contains(event.pos()):
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# OrderTableSettingsDialog
# ─────────────────────────────────────────────────────────────────────────────

class OrderTableSettingsDialog(BaseThemedDialog):
    """Real-time column show/hide for the Orders table."""

    COLUMNS: list[tuple[str, str, str]] = [
        ("Entry Value",  "Entry Value",  "💲 Entry Value"),
        ("Swap",         "SWAP",         "⇄ Swap"),
        ("Market Value", "Market Value", "📈 Market Value"),
        ("Commission",   "Commission",   "％ Commission"),
        ("P/L in %",     "P/L IN %",     "🥧 P/L in %"),
        ("Remarks",      "Remarks",      "📝 Remark"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent, title="Table Settings")
        self._tv = table_view
        self._cfg = _load(
            _ORDER_CFG,
            [key for key, _, _ in self.COLUMNS] + ["Multi-Target SL/TP"],
            default=False,
        )
        self._build()
        self._apply_all()

    def _build(self):
        sec1 = QLabel("VISIBLE OPTIONS")
        sec1.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        for i, (key, header, display) in enumerate(self.COLUMNS):
            cb = self._make_cb(key, header, display)
            grid.addWidget(cb, i // 2, i % 2)
        self.content_layout.addLayout(grid)

        self.content_layout.addSpacing(6)

        sec2 = QLabel("👑 MASTER FEATURES")
        sec2.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec2)

        cb_m = QCheckBox("🎯 Multi-Target SL/TP")
        cb_m.setChecked(bool(self._cfg.get("Multi-Target SL/TP", False)))
        cb_m.setCursor(Qt.PointingHandCursor)
        cb_m.toggled.connect(lambda checked: self._persist_only("Multi-Target SL/TP", checked))
        self.content_layout.addWidget(cb_m)

    def _make_cb(self, key: str, header: str, display: str) -> QCheckBox:
        cb = QCheckBox(display)
        cb.blockSignals(True)
        cb.setChecked(bool(self._cfg.get(key, False)))
        cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        cb.toggled.connect(lambda checked, k=key, hdr=header: self._on_toggle(k, hdr, checked))
        return cb

    def _on_toggle(self, key: str, header: str, checked: bool) -> None:
        self._cfg[key] = checked
        _save(_ORDER_CFG, self._cfg)
        tv = self._get_tv()
        if tv: _set_visible(tv, header, checked)

    def _persist_only(self, key: str, checked: bool) -> None:
        self._cfg[key] = checked
        _save(_ORDER_CFG, self._cfg)

    def _get_tv(self):
        if self._tv is not None: return self._tv
        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "orders_tab", "table", "table_view"),
                ("table", "table_view"),
            ):
                try:
                    obj = p
                    for attr in path: obj = getattr(obj, attr)
                    if obj is not None:
                        self._tv = obj
                        return obj
                except AttributeError: pass
            try: p = p.parent()
            except Exception: break
        return None

    def _apply_all(self):
        tv = self._get_tv()
        if tv is None: return
        for key, header, _ in self.COLUMNS:
            _set_visible(tv, header, bool(self._cfg.get(key, False)))


# ─────────────────────────────────────────────────────────────────────────────
# HistoryTableSettingsDialog
# ─────────────────────────────────────────────────────────────────────────────

class HistoryTableSettingsDialog(BaseThemedDialog):
    """Real-time column show/hide for the History table."""

    COLUMNS: list[tuple[str, str, str]] = [
        ("Entry Value",  "Entry Value",  "💲 Entry Value"),
        ("Swap",         "SWAP",         "⇄ Swap"),
        ("Closed Value", "Closed Value", "📈 Closed Value"),
        ("Commission",   "Commission",   "％ Commission"),
        ("P/L in %",     "P/L IN %",     "🥧 P/L in %"),
        ("Remark",       "Remark",       "📝 Remark"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent, title="Table Settings")
        self._tv = table_view
        self._cfg = _load(
            _HIST_CFG,
            [key for key, _, _ in self.COLUMNS],
            default=False,
        )
        self._build()
        self._apply_all()

    def _build(self):
        sec1 = QLabel("VISIBLE OPTIONS")
        sec1.setObjectName("SectionTitle")
        self.content_layout.addWidget(sec1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        for i, (key, header, display) in enumerate(self.COLUMNS):
            cb = self._make_cb(key, header, display)
            grid.addWidget(cb, i // 2, i % 2)
        self.content_layout.addLayout(grid)

    def _make_cb(self, key: str, header: str, display: str) -> QCheckBox:
        cb = QCheckBox(display)
        cb.blockSignals(True)
        cb.setChecked(bool(self._cfg.get(key, False)))
        cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        cb.toggled.connect(lambda checked, k=key, hdr=header: self._on_toggle(k, hdr, checked))
        return cb

    def _on_toggle(self, key: str, header: str, checked: bool) -> None:
        self._cfg[key] = checked
        _save(_HIST_CFG, self._cfg)
        tv = self._get_tv()
        if tv: _set_visible(tv, header, checked)

    def _get_tv(self):
        if self._tv is not None: return self._tv
        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "history_tab", "view"),
                ("orders_widget", "history_tab", "table_view"),
                ("table", "table_view"),
            ):
                try:
                    obj = p
                    for attr in path: obj = getattr(obj, attr)
                    if obj is not None:
                        self._tv = obj
                        return obj
                except AttributeError: pass
            try: p = p.parent()
            except Exception: break
        return None

    def _apply_all(self):
        tv = self._get_tv()
        if tv is None: return
        for key, header, _ in self.COLUMNS:
            _set_visible(tv, header, bool(self._cfg.get(key, False)))