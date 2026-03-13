"""
theme_popup.py  –  "Theme Settings" slide-in panel.

ROOT CAUSES fixed (v4):
  ✅ Panel is now a CHILD QWidget (not Qt.Tool window)
     → combos open as normal system popups, no clipping/overflow
     → panel stays within parent app, never floats over other apps
  ✅ ToggleSwitch drawn with paintEvent() — always visible
  ✅ Dark Theme row present and functional
  ✅ Period selector: QComboBox (matches reference)
  ✅ Sub-theme: QComboBox (matches reference)
  ✅ Correct sizing: H_CRAZY=510, H_TIME=460, H_COMPACT=330
  ✅ Slide animation preserved
  ✅ Click-outside-to-close preserved via parent eventFilter
"""
from __future__ import annotations
from typing import Dict

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QTime,
    Signal, QPoint, QEvent,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QFrame, QComboBox, QTimeEdit,
    QGraphicsDropShadowEffect, QSizePolicy, QScrollArea,
    QApplication,
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath,
)

from .theme_manager import ThemeManager
from .theme_state import (
    CRAZY_COLORS, TIME_PERIODS, friendly_name, get_active_time_period,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PANEL_W   = 290   # same width for ALL theme modes
H_COMPACT = 300   # system / dark / light rows only
H_CRAZY   = 510   # crazy + swatch grid
H_TIME    = 520   # time-based: 5 rows + badge + combo + period card

_SUB_THEME_OPTIONS = [
    ("Light Theme",   "light"),
    ("Dark Theme",    "dark"),
    ("Red Accent",    "crazy_red"),
    ("Green Accent",  "crazy_green"),
    ("Purple Accent", "crazy_purple"),
    ("Orange Accent", "crazy_orange"),
    ("Yellow Accent", "crazy_yellow"),
    ("Blue Accent",   "crazy_blue"),
]

_PERIOD_KEYS = list(TIME_PERIODS.keys())   # morning, afternoon, evening, night


# ---------------------------------------------------------------------------
# ToggleSwitch — painted in paintEvent, never relies on stylesheet background
# ---------------------------------------------------------------------------
class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    @property
    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, value: bool, emit: bool = True):
        if self._checked == value:
            return
        self._checked = value
        self.update()
        if emit:
            self.toggled.emit(value)

    def _refresh_style(self):
        self.update()

    def mousePressEvent(self, event):
        self.set_checked(True)

    def paintEvent(self, event):
        mgr = ThemeManager.instance()
        t   = mgr.tokens()
        on_color  = t.get("bg_toggle_on",  "#1976d2")
        off_color = t.get("bg_toggle_off", "#cbd5e0")

        w, h   = self.width(), self.height()
        radius = h / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Track
        painter.setBrush(QBrush(QColor(on_color if self._checked else off_color)))
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, radius, radius)
        painter.drawPath(path)

        # Knob
        m      = 3
        knob_d = h - m * 2
        knob_x = (w - knob_d - m) if self._checked else m
        painter.setPen(QPen(QColor(0, 0, 0, 25), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(int(knob_x), m, knob_d, knob_d)
        painter.end()


# ---------------------------------------------------------------------------
# Circle Swatch Button
# ---------------------------------------------------------------------------
_SWATCH_COLORS = {
    "red":    ("#e53935", "Red"),
    "green":  ("#2e7d32", "Green"),
    "purple": ("#7c3aed", "Purple"),
    "orange": ("#f97316", "Orange"),
    "yellow": ("#d97706", "Yellow"),
    "blue":   ("#1d4ed8", "Blue"),
}


class SwatchButton(QPushButton):
    def __init__(self, color_name: str, parent=None):
        super().__init__(parent)
        self._color_name = color_name
        self._hex, self._label = _SWATCH_COLORS.get(
            color_name, ("#1976d2", color_name.capitalize())
        )
        self.setFixedSize(72, 84)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy, r = 36, 32, 25

        if self.isChecked():
            glow = QColor(self._hex)
            glow.setAlpha(80)
            painter.setPen(QPen(glow, 5))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - r - 5, cy - r - 5, (r + 5) * 2, (r + 5) * 2)
            painter.setPen(QPen(QColor(self._hex), 2))
            painter.drawEllipse(cx - r - 3, cy - r - 3, (r + 3) * 2, (r + 3) * 2)

        gradient = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        base = QColor(self._hex)
        gradient.setColorAt(0, base.lighter(125))
        gradient.setColorAt(1, base)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        if self.isChecked():
            pen = QPen(QColor("white"), 2.5)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(cx - 7, cy, cx - 2, cy + 6)
            painter.drawLine(cx - 2, cy + 6, cx + 7, cy - 5)

        t = ThemeManager.instance().tokens()
        painter.setPen(QColor(t.get("text_secondary", "#555555")))
        f = self.font()
        f.setPointSize(9)
        painter.setFont(f)
        from PySide6.QtCore import QRect as _R
        painter.drawText(_R(0, 64, 72, 18), Qt.AlignCenter, self._label)
        painter.end()


# ---------------------------------------------------------------------------
# TimePeriodCard
# ---------------------------------------------------------------------------
class TimePeriodCard(QWidget):
    period_changed = Signal(str, str)

    def __init__(self, period_key: str, parent=None):
        super().__init__(parent)
        self._key  = period_key
        info       = TIME_PERIODS[period_key]
        mgr        = ThemeManager.instance()
        t          = mgr.tokens()

        bg       = t.get("bg_widget",      "#ffffff")
        text     = t.get("text_primary",   "#1a202c")
        bdr      = t.get("border_primary", "#e5e7eb")
        text2    = t.get("text_secondary", "#4a5568")
        accent   = t.get("accent",         "#1976d2")
        bg_inp   = t.get("bg_input",       "#f5f7fa")
        positive = t.get("text_positive",  "#16a34a")
        acc_t    = t.get("accent_text",    "#ffffff")

        self.setStyleSheet(f"""
            TimePeriodCard {{
                background: {bg};
                border: 1px solid {bdr};
                border-radius: 10px;
            }}
            QTimeEdit {{
                background: {bg_inp};
                color: {text};
                border: 1px solid {bdr};
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 11px;
            }}
            QComboBox {{
                background-color: {bg_inp};
                color: {text};
                border: 1px solid {bdr};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background-color: {bg};
                color: {text};
                border: 1px solid {bdr};
                selection-background-color: {accent};
                selection-color: {acc_t};
                outline: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        top = QHBoxLayout()
        is_active = (get_active_time_period() == period_key)
        lbl = QLabel(f"{info['icon']}  {info['label']}")
        lbl.setStyleSheet(
            f"font-weight: 700; font-size: 12px; "
            f"color: {positive if is_active else text}; background: transparent;"
        )
        top.addWidget(lbl)
        top.addStretch()
        if is_active:
            dot = QLabel("● Active")
            dot.setStyleSheet(
                f"color: {positive}; font-size: 10px; font-weight: 600; "
                f"background: rgba(22,163,74,0.12); border-radius: 4px; padding: 2px 6px;"
            )
            top.addWidget(dot)
        layout.addLayout(top)

        # Time range
        # Time row: each field is a styled frame containing QTimeEdit + clock icon
        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        time_row.setContentsMargins(0, 0, 0, 0)

        def _make_time_field(time_val):
            """Wrap a QTimeEdit + clock icon in a bordered frame to match reference."""
            frame = QFrame(self)
            frame.setFixedWidth(88)
            frame.setFixedHeight(28)
            frame.setStyleSheet(
                f"QFrame {{ background-color: {bg_inp}; border: 1px solid {bdr}; "
                f"border-radius: 5px; }}"
            )
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(5, 0, 4, 0)
            fl.setSpacing(2)
            te = QTimeEdit(time_val, frame)
            te.setDisplayFormat("hh:mm AP")
            te.setFixedHeight(24)
            # te.setMinimumWidth(0)
            te.setFixedWidth(55)
            te.setStyleSheet(
                "QTimeEdit { border: none; background: transparent; "
                "font-size: 11px; padding: 0; }"
                "QTimeEdit::up-button   { width: 0; height: 0; border: none; }"
                "QTimeEdit::down-button { width: 0; height: 0; border: none; }"
            )
            clock = QLabel("🕐", frame)
            clock.setStyleSheet(
                "background: transparent; border: none; font-size: 12px;"
            )
            clock.setFixedWidth(16)
            fl.addWidget(te)
            fl.addWidget(clock)
            return frame, te

        start_frame, self._start = _make_time_field(
            QTime.fromString(info["start"], "HH:mm"))
        end_frame,   self._end   = _make_time_field(
            QTime.fromString(info["end"],   "HH:mm"))

        arrow = QLabel("to")
        arrow.setStyleSheet(
            f"color: {text2}; background: transparent; font-size: 11px; font-weight: 500;"
        )
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setFixedWidth(20)

        time_row.addWidget(start_frame)
        time_row.addWidget(arrow)
        time_row.addWidget(end_frame)
        time_row.addStretch()
        layout.addLayout(time_row)

        # Sub-theme combo
        self._combo = QComboBox(self)
        for display, value in _SUB_THEME_OPTIONS:
            self._combo.addItem(display, value)
        current_sub = mgr.get_time_period_sub_theme(period_key)
        for i, (_, val) in enumerate(_SUB_THEME_OPTIONS):
            if val == current_sub:
                self._combo.setCurrentIndex(i)
                break
        self._combo.currentIndexChanged.connect(self._on_sub_changed)
        # Force dropdown view opaque
        _sv = self._combo.view()
        _sv.setAutoFillBackground(True)
        _sv.setAttribute(Qt.WA_TranslucentBackground, False)
        layout.addWidget(self._combo)

    def _on_sub_changed(self, idx: int):
        sub = self._combo.itemData(idx)
        ThemeManager.instance().set_time_period_override(self._key, sub)
        self.period_changed.emit(self._key, sub)


# ---------------------------------------------------------------------------
# Main Popup Panel — CHILD widget (not Qt.Tool), stays within parent app
# ---------------------------------------------------------------------------
class ThemePopup(QWidget):
    """
    Slide-in panel rendered as a child of the parent widget.

    KEY DESIGN:
      • No Qt.Tool / Qt.WindowStaysOnTopHint — prevents floating over other apps
      • raise_() is used so it appears above siblings (chart, panels etc.)
      • QComboBox dropdowns work as normal system popups — no overflow/clipping
      • click-outside-to-close via parent's eventFilter
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # No window flags — pure child widget.
        # WA_TranslucentBackground makes the region outside the card fully
        # transparent so no coloured rectangle appears around the panel.
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._mgr = ThemeManager.instance()
        self._visible = False
        self._rows:        Dict[str, tuple]         = {}
        self._toggles:     Dict[str, ToggleSwitch]  = {}
        self._swatch_btns: Dict[str, SwatchButton]  = {}
        self._current_period_widget = None
        self._anim = None

        self._build_ui()
        self._refresh_styles()
        self._mgr.theme_changed.connect(lambda name, t: self._refresh_styles())

        # Install on QApplication so clicks on ANY widget in the window
        # (chart, panels, toolbars, etc.) trigger close — not just the parent.
        QApplication.instance().installEventFilter(self)

        # Child widgets are visible by default — hide until show_popup() is called
        self.hide()

    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if (
            event.type() == QEvent.MouseButtonPress
            and self._visible
            and self.isVisible()
        ):
            # obj is whatever widget was clicked; map its click position to
            # global coords so we can compare against our own global rect.
            try:
                local_pos = event.position().toPoint()
            except AttributeError:
                local_pos = event.pos()

            if isinstance(obj, QWidget):
                global_pos = obj.mapToGlobal(local_pos)
            else:
                global_pos = local_pos

            popup_global = QRect(
                self.mapToGlobal(self.rect().topLeft()),
                self.size(),
            )

            # Only close if the click is in the same top-level window
            # but outside the popup panel itself.
            top_level = self.window()
            clicked_top = obj.window() if isinstance(obj, QWidget) else None
            if clicked_top is top_level and not popup_global.contains(global_pos):
                self.hide_popup()

        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self._card = QFrame(self)
        self._card.setObjectName("ThemeCard")

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self._card.setGraphicsEffect(shadow)
        outer.addWidget(self._card)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(16, 14, 16, 12)
        card_layout.setSpacing(3)

        # ── Header ──────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Theme Settings")
        title.setObjectName("ThemeTitle")
        self._subtitle = QLabel("Current: System Default")
        self._subtitle.setObjectName("ThemeSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(self._subtitle)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setObjectName("ThemeCloseBtn")
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self.hide_popup)

        hdr.addLayout(title_col)
        hdr.addStretch()
        hdr.addWidget(self._close_btn)
        card_layout.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("ThemeSep")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)
        card_layout.addSpacing(4)

        # ── Scrollable body ─────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent;")

        body = QWidget()
        body.setObjectName("ThemeBody")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 0, 4, 0)
        self._body_layout.setSpacing(2)
        scroll.setWidget(body)
        card_layout.addWidget(scroll)

        # ── Theme rows ───────────────────────────────────────────────
        for icon, label, key in [
            ("🖥",  "System Default",    "system"),
            ("🌙",  "Dark Theme",        "dark"),
            ("☀️", "Light Theme",       "light"),
            ("🎨",  "Crazy Theme",       "crazy"),
        ]:
            self._add_theme_row(icon, label, key)

        # ── Crazy swatch grid ────────────────────────────────────────
        self._swatch_frame = QFrame()
        self._swatch_frame.setObjectName("SwatchFrame")
        sf_lay = QVBoxLayout(self._swatch_frame)
        sf_lay.setContentsMargins(10, 10, 10, 10)
        sf_lay.setSpacing(6)

        sw_lbl = QLabel("SELECTED COLOR THEME")
        sw_lbl.setObjectName("SwatchLabel")
        sf_lay.addWidget(sw_lbl)

        row_top = QHBoxLayout()
        row_bot = QHBoxLayout()
        row_top.setSpacing(2)
        row_bot.setSpacing(2)
        self._swatch_group = QButtonGroup(self)
        self._swatch_group.setExclusive(True)

        for i, name in enumerate(CRAZY_COLORS):
            btn = SwatchButton(name, self)
            self._swatch_group.addButton(btn)
            self._swatch_btns[name] = btn
            (row_top if i < 3 else row_bot).addWidget(btn)
            btn.clicked.connect(lambda _, n=name: self._on_swatch(n))

        row_top.addStretch()
        row_bot.addStretch()
        sf_lay.addLayout(row_top)
        sf_lay.addLayout(row_bot)
        self._body_layout.addWidget(self._swatch_frame)
        self._swatch_frame.hide()

        # ── Time-Based row ───────────────────────────────────────────
        self._add_theme_row("🕐", "Time-Based Theme", "time")

        # ── Time period configurator ─────────────────────────────────
        self._time_frame = QFrame()
        self._time_frame.setObjectName("TimeFrame")
        tf_lay = QVBoxLayout(self._time_frame)
        tf_lay.setContentsMargins(8, 8, 8, 6)
        tf_lay.setSpacing(6)

        self._active_period_label = QLabel()
        self._active_period_label.setObjectName("ActivePeriodLabel")
        tf_lay.addWidget(self._active_period_label)

        period_sel_lbl = QLabel("Select Period to Configure")
        period_sel_lbl.setObjectName("PeriodSelectLabel")
        tf_lay.addWidget(period_sel_lbl)

        # Period combo (QComboBox — now works correctly as child widget)
        self._period_combo = QComboBox()
        self._period_combo.setObjectName("PeriodCombo")
        for k, v in TIME_PERIODS.items():
            self._period_combo.addItem(f"{v['icon']}  {v['label']}", k)
        self._period_combo.currentIndexChanged.connect(self._on_period_combo_changed)
        # Force dropdown view opaque — prevents content behind it bleeding through
        _cv = self._period_combo.view()
        _cv.setAutoFillBackground(True)
        _cv.setAttribute(Qt.WA_TranslucentBackground, False)
        tf_lay.addWidget(self._period_combo)

        # Period card container
        self._period_row_container = QWidget()
        self._period_row_container.setStyleSheet("background: transparent;")
        self._period_row_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._period_row_layout = QVBoxLayout(self._period_row_container)
        self._period_row_layout.setContentsMargins(0, 0, 0, 0)
        self._period_row_layout.setSpacing(0)
        tf_lay.addWidget(self._period_row_container)

        self._body_layout.addWidget(self._time_frame)
        self._time_frame.hide()

        self._body_layout.addStretch()
        self._sync_toggles()

    # ------------------------------------------------------------------
    def _add_theme_row(self, icon: str, label: str, key: str):
        row_w = QWidget()
        row_w.setCursor(Qt.PointingHandCursor)
        row_lay = QHBoxLayout(row_w)
        row_lay.setContentsMargins(4, 7, 4, 7)
        row_lay.setSpacing(10)

        ico = QLabel(icon)
        ico.setFixedWidth(24)
        ico.setObjectName("RowIcon")
        ico.setStyleSheet("font-size: 16px; background: transparent;")

        txt = QLabel(label)
        txt.setObjectName("RowLabel")
        txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        tog = ToggleSwitch(parent=self)
        self._toggles[key] = tog

        row_lay.addWidget(ico)
        row_lay.addWidget(txt)
        row_lay.addWidget(tog)

        row_w.mousePressEvent = lambda e, k=key, t=tog: t.set_checked(not t.is_checked)
        self._body_layout.addWidget(row_w)
        self._rows[key] = (row_w, tog)
        tog.toggled.connect(lambda on, k=key: self._on_toggle(k, on))

    # ------------------------------------------------------------------
    def _on_toggle(self, key: str, on: bool):
        if not on:
            return
        for k, tog in self._toggles.items():
            if k != key and tog.is_checked:
                tog.set_checked(False, emit=False)

        self._swatch_frame.setVisible(key == "crazy")
        self._time_frame.setVisible(key == "time")

        if key == "crazy":
            color = self._mgr.crazy_color
            self._mgr.apply_theme(f"crazy_{color}")
            btn = self._swatch_btns.get(color)
            if btn:
                btn.setChecked(True)
        else:
            self._mgr.apply_theme(key)

        if key == "time":
            self._update_active_period_label()
            self._period_combo.setCurrentIndex(0)
            self._load_period_card(_PERIOD_KEYS[0])

        self._resize_to_content(key)
        self._subtitle.setText(f"Current: {self._mgr.friendly_current()}")
        QApplication.processEvents()
        self._refresh_styles()

    def _on_swatch(self, color: str):
        self._mgr.set_crazy_color(color)
        self._subtitle.setText(f"Current: {friendly_name('crazy_' + color)}")
        self._refresh_styles()

    def _on_period_combo_changed(self, idx: int):
        key = self._period_combo.itemData(idx)
        if key:
            self._load_period_card(key)

    def _load_period_card(self, key: str):
        if self._current_period_widget:
            self._period_row_layout.removeWidget(self._current_period_widget)
            self._current_period_widget.deleteLater()
            self._current_period_widget = None
        card = TimePeriodCard(key, self._period_row_container)
        self._period_row_layout.addWidget(card)
        self._current_period_widget = card

    def _sync_toggles(self):
        theme    = self._mgr.current_theme
        is_crazy = theme.startswith("crazy")
        active   = "crazy" if is_crazy else theme

        for k, tog in self._toggles.items():
            tog.set_checked(k == active, emit=False)

        self._swatch_frame.setVisible(is_crazy)
        if is_crazy:
            btn = self._swatch_btns.get(self._mgr.crazy_color)
            if btn:
                btn.setChecked(True)

        is_time = (theme == "time")
        self._time_frame.setVisible(is_time)
        if is_time:
            self._update_active_period_label()
            self._period_combo.setCurrentIndex(0)
            self._load_period_card(_PERIOD_KEYS[0])

        self._subtitle.setText(f"Current: {self._mgr.friendly_current()}")
        self._resize_to_content(active)
        QApplication.processEvents()

    def _update_active_period_label(self):
        period = get_active_time_period()
        info   = TIME_PERIODS[period]
        self._active_period_label.setText(f"● {info['label']} is currently active")

    # ------------------------------------------------------------------
    def _resize_to_content(self, active_key: str = "system"):
        if not self.parent():
            return
        p  = self.parent()
        ph = p.height()
        if active_key == "time":
            h = min(H_TIME, ph - 60)
            w = PANEL_W + 12
        elif active_key == "crazy":
            h = min(H_CRAZY, ph - 80)
            w = PANEL_W + 12
        else:
            h = min(H_COMPACT, ph - 80)
            w = PANEL_W + 12
        x = p.width() - w - 10
        self.setGeometry(x, self.y(), w, h)

    # ------------------------------------------------------------------
    @staticmethod
    def _force_combo_opaque(combo: 'QComboBox', bg: str, text: str,
                             border: str, accent: str, acc_t: str = "#ffffff"):
        """Programmatically force combo view background — stylesheet alone
        can be transparent on some Qt builds / platform styles."""
        from PySide6.QtGui import QPalette
        view = combo.view()
        view.setAutoFillBackground(True)
        view.setAttribute(Qt.WA_TranslucentBackground, False)
        pal = view.palette()
        pal.setColor(QPalette.Base,   QColor(bg))
        pal.setColor(QPalette.Window, QColor(bg))
        pal.setColor(QPalette.Text,   QColor(text))
        pal.setColor(QPalette.Highlight,     QColor(accent))
        pal.setColor(QPalette.HighlightedText, QColor(acc_t))
        view.setPalette(pal)
        view.setStyleSheet(
            f"QAbstractItemView {{"
            f"  background-color: {bg};"
            f"  color: {text};"
            f"  border: 1px solid {border};"
            f"  border-radius: 6px;"
            f"  selection-background-color: {accent};"
            f"  selection-color: {acc_t};"
            f"  outline: none;"
            f"  padding: 2px;"
            f"}}"
        )

    # ------------------------------------------------------------------
    def _refresh_styles(self):
        t = self._mgr.tokens()
        r      = t.get("popup_border_radius", "12px")
        border = t.get("popup_border",        "#e5e7eb")
        bg     = t.get("bg_popup",            "#ffffff")
        text   = t.get("text_primary",        "#1a202c")
        text2  = t.get("text_secondary",      "#4a5568")
        bg_btn = t.get("bg_button",           "#f0f4f8")
        bg_bth = t.get("bg_button_hover",     "#e2e8f0")
        sep_c  = t.get("border_separator",    "#e5e7eb")
        bg_inp = t.get("bg_input",            "#f5f7fa")
        accent = t.get("accent",              "#1976d2")
        bg_hdr = t.get("bg_header",           "#f5f7fa")
        acc_t  = t.get("accent_text",         "#ffffff")
        pos    = t.get("text_positive",       "#16a34a")

        self._card.setStyleSheet(f"""
            QFrame#ThemeCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {r};
            }}
            QLabel#ThemeTitle {{
                font-size: 15px; font-weight: 700;
                color: {text}; background: transparent;
            }}
            QLabel#ThemeSubtitle {{
                font-size: 11px; color: {text2}; background: transparent;
            }}
            QFrame#ThemeSep {{
                background: {sep_c}; border: none;
                min-height: 1px; max-height: 1px;
            }}
            QPushButton#ThemeCloseBtn {{
                background: {bg_btn};
                border: 1px solid {sep_c};
                border-radius: 15px;
                color: {text2}; font-size: 12px; font-weight: 600;
            }}
            QPushButton#ThemeCloseBtn:hover {{
                background: {bg_bth}; color: {text};
            }}
            QLabel#SwatchLabel {{
                font-size: 10px; font-weight: 700;
                letter-spacing: 1.2px; color: {text2}; background: transparent;
            }}
            QFrame#SwatchFrame {{
                background: {bg_hdr};
                border: 1px solid {border};
                border-radius: 10px;
                margin-left: 2px; margin-right: 2px;
            }}
            QFrame#TimeFrame {{
                background: {bg_hdr};
                border: 1px solid {border};
                border-radius: 10px;
                margin-left: 2px; margin-right: 2px;
            }}
            QLabel#ActivePeriodLabel {{
                color: {pos}; font-weight: 700; font-size: 11px;
                background: rgba(22,163,74,0.1);
                border-radius: 6px; padding: 5px 10px;
                border: 1px solid rgba(22,163,74,0.25);
            }}
            QLabel#PeriodSelectLabel {{
                font-size: 11px; font-weight: 600;
                color: {text}; background: transparent;
            }}
            QLabel#RowLabel {{
                font-size: 13px; font-weight: 500;
                color: {text}; background: transparent;
            }}
            QLabel#RowIcon {{ background: transparent; }}
            QLabel {{ color: {text}; background: transparent; }}
            QComboBox#PeriodCombo {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QComboBox#PeriodCombo::drop-down {{
                border: none; width: 24px;
            }}
            QComboBox#PeriodCombo QAbstractItemView {{
                background-color: {bg}; color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                selection-background-color: {accent};
                selection-color: {acc_t};
                outline: none; padding: 2px;
            }}
            QTimeEdit {{
                background: {bg_inp}; color: {text};
                border: 1px solid {border};
                border-radius: 5px; padding: 3px 6px; font-size: 11px;
            }}
            QWidget#ThemeBody {{ background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 5px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {sep_c}; border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        for tog in self._toggles.values():
            tog._refresh_style()

        # Force period combo dropdown to use opaque solid background
        # (stylesheet alone is not always enough on all platforms)
        self._force_combo_opaque(self._period_combo, bg, text, border, accent, acc_t)

    # ------------------------------------------------------------------
    def show_popup(self):
        p = self.parent()
        if not p:
            self.show()
            return

        pw, ph = p.width(), p.height()
        theme  = self._mgr.current_theme
        if theme.startswith("crazy"):
            h = min(H_CRAZY, ph - 80)
            w = PANEL_W + 12
        elif theme == "time":
            h = min(H_TIME, ph - 60)
            w = PANEL_W + 12
        else:
            h = min(H_COMPACT, ph - 80)
            w = PANEL_W + 12
        start_rect = QRect(pw, 60, w, h)
        end_rect   = QRect(pw - w - 10, 60, w, h)

        self.setGeometry(start_rect)
        self._sync_toggles()
        self.show()
        self.raise_()          # float above the chart and all sibling widgets

        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(240)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)
        anim.finished.connect(self.raise_)   # re-raise after slide completes
        anim.start()
        self._anim    = anim
        self._visible = True

    def hide_popup(self):
        p = self.parent()
        if not p:
            self.hide()
            self._visible = False
            return

        end_rect = QRect(p.width() + 10, self.y(), self.width(), self.height())
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.setStartValue(self.geometry())
        anim.setEndValue(end_rect)
        anim.finished.connect(self.hide)
        anim.start()
        self._anim    = anim
        self._visible = False

    def toggle_popup(self):
        if self._visible and self.isVisible():
            self.hide_popup()
        else:
            self.show_popup()