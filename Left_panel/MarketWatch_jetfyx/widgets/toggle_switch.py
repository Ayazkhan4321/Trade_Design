"""
toggle_switch.py  –  iOS-style sliding toggle switch.

Matches the reference screenshot:
  • Rounded pill track
  • White circular knob that slides left (OFF) / right (ON)
  • Accent/blue track when ON, muted grey track when OFF
  • Smooth knob position, drop-shadow on knob
  • Theme-aware: reads tokens from ThemeManager if available
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPointF
from PySide6.QtGui  import (
    QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath,
)
from PySide6.QtWidgets import QWidget

try:
    from Theme.theme_manager import ThemeManager as _ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _ThemeManager    = None
    _THEME_AVAILABLE = False


class ToggleSwitch(QWidget):
    """
    Drop-in replacement for any ToggleSwitch widget.

    Public API (same as the original):
        toggled(bool)       — signal
        isChecked() → bool
        setChecked(bool)
        toggle()
    """

    toggled = Signal(bool)

    # ------------------------------------------------------------------
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def isChecked(self) -> bool:
        return self._checked

    # alias used by theme_popup style (is_checked property)
    @property
    def is_checked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool):
        if self._checked == value:
            return
        self._checked = value
        self.update()
        self.toggled.emit(value)

    # alias used by theme_popup (set_checked with optional emit kwarg)
    def set_checked(self, value: bool, emit: bool = True):
        if self._checked == value:
            return
        self._checked = value
        self.update()
        if emit:
            self.toggled.emit(value)

    def toggle(self):
        self.setChecked(not self._checked)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()

    # ------------------------------------------------------------------
    # Token helper
    # ------------------------------------------------------------------
    def _tokens(self) -> dict:
        if _THEME_AVAILABLE:
            try:
                return _ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    # ------------------------------------------------------------------
    # Paint — iOS-style track + knob
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        t = self._tokens()

        on_track  = t.get("bg_toggle_on",  "#1a8cff")   # blue accent
        off_track = t.get("bg_toggle_off", "#3a3f4b")   # dark muted grey

        w, h   = self.width(), self.height()
        radius = h / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ── Track ──────────────────────────────────────────────────────
        track_color = QColor(on_track if self._checked else off_track)

        # Subtle vertical gradient on the track
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, track_color.lighter(110))
        grad.setColorAt(1.0, track_color)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.drawPath(track_path)

        # ── Knob ───────────────────────────────────────────────────────
        m      = 3                          # margin from edge
        knob_d = h - m * 2                 # knob diameter
        knob_x = float(w - knob_d - m) if self._checked else float(m)
        knob_y = float(m)

        # Knob shadow (drawn slightly larger, semi-transparent dark circle)
        shadow_color = QColor(0, 0, 0, 50)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(
            QRectF(knob_x + 0.5, knob_y + 1.5, knob_d, knob_d)
        )

        # Knob face — radial gradient for subtle 3-D lift
        rg = QRadialGradient(
            QPointF(knob_x + knob_d * 0.38, knob_y + knob_d * 0.32),
            knob_d * 0.65,
        )
        rg.setColorAt(0.0, QColor("#ffffff"))
        rg.setColorAt(1.0, QColor("#dde3ec"))

        painter.setBrush(QBrush(rg))
        painter.setPen(QPen(QColor(200, 200, 200, 80), 0.5))
        painter.drawEllipse(QRectF(knob_x, knob_y, knob_d, knob_d))

        painter.end()