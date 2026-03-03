"""
theme_manager.py  –  Singleton that owns the active theme and notifies listeners.

Usage:
    from Theme.theme_manager import ThemeManager
    mgr = ThemeManager.instance()
    mgr.apply_theme("dark")
    mgr.theme_changed.connect(my_callback)   # callback(theme_name, tokens)
"""
from __future__ import annotations
import json, os, logging
from typing import Callable, Dict, List

from PySide6.QtCore import QObject, Signal, QTimer

from .theme_state import get_tokens, friendly_name, get_active_time_period, TIME_PERIODS

LOG = logging.getLogger(__name__)

_PREFS_FILE = os.path.join(os.path.dirname(__file__), "_theme_prefs.json")


class ThemeManager(QObject):
    """Global singleton.  Emit theme_changed when the active theme changes."""

    theme_changed = Signal(str, dict)  # (theme_name, tokens)

    _instance: "ThemeManager | None" = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme: str = "dark"
        self._crazy_color: str = "red"     # active colour for crazy themes
        self._time_period_overrides: Dict[str, str] = {}  # period -> sub_theme override
        self._listeners: List[Callable] = []

        # Time-based auto-switcher
        self._time_timer = QTimer(self)
        self._time_timer.setInterval(60_000)  # check every minute
        self._time_timer.timeout.connect(self._auto_time_check)

        self._load_prefs()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def crazy_color(self) -> str:
        return self._crazy_color

    def apply_theme(self, theme_name: str, crazy_color: str | None = None):
        """Switch to *theme_name*.  Persist and notify all listeners."""
        self._current_theme = theme_name
        if crazy_color is not None:
            self._crazy_color = crazy_color
        if theme_name.startswith("crazy"):
            theme_name = f"crazy_{self._crazy_color}"
            self._current_theme = theme_name

        self._save_prefs()

        # tokens = get_tokens(theme_name)
        tokens = self.tokens()
        self.theme_changed.emit(theme_name, tokens)
        for cb in self._listeners:
            try:
                cb(theme_name, tokens)
            except Exception:
                LOG.exception("Theme listener raised")

        # Enable / disable auto-switcher
        if theme_name == "time":
            self._time_timer.start()
        else:
            self._time_timer.stop()

    def set_crazy_color(self, color: str):
        """Change the crazy-theme accent colour and re-apply if currently in crazy mode."""
        self._crazy_color = color
        if "crazy" in self._current_theme:
            self.apply_theme(f"crazy_{color}")
        else:
            self._save_prefs()

    def set_time_period_override(self, period: str, sub_theme: str):
        """Override the sub-theme (light/dark) for a specific time period."""
        self._time_period_overrides[period] = sub_theme
        self._save_prefs()
        if self._current_theme == "time":
            self._auto_time_check()

    def get_time_period_sub_theme(self, period: str) -> str:
        if period in self._time_period_overrides:
            return self._time_period_overrides[period]
        return TIME_PERIODS.get(period, {}).get("sub_theme", "dark")

    def tokens(self) -> Dict[str, str]:
        """Return the current token dict without triggering a full apply."""
        effective = self._current_theme
        if effective == "time":
            period = get_active_time_period()
            effective = self.get_time_period_sub_theme(period)
        return get_tokens(effective)

    def register_listener(self, cb: Callable):
        """Register a plain callable(theme_name, tokens) listener."""
        if cb not in self._listeners:
            self._listeners.append(cb)

    def unregister_listener(self, cb: Callable):
        self._listeners = [x for x in self._listeners if x is not cb]

    def friendly_current(self) -> str:
        return friendly_name(self._current_theme)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _auto_time_check(self):
        if self._current_theme != "time":
            return
        period = get_active_time_period()
        sub = self.get_time_period_sub_theme(period)
        tokens = get_tokens(sub)
        self.theme_changed.emit("time", tokens)
        for cb in self._listeners:
            try:
                cb("time", tokens)
            except Exception:
                LOG.exception("Time-theme listener raised")

    def _save_prefs(self):
        try:
            data = {
                "theme": self._current_theme,
                "crazy_color": self._crazy_color,
                "time_period_overrides": self._time_period_overrides,
            }
            with open(_PREFS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            LOG.debug("Could not save theme prefs")

    def _load_prefs(self):
        try:
            if os.path.exists(_PREFS_FILE):
                with open(_PREFS_FILE) as f:
                    data = json.load(f)
                self._current_theme = data.get("theme", "dark")
                self._crazy_color = data.get("crazy_color", "red")
                self._time_period_overrides = data.get("time_period_overrides", {})
        except Exception:
            LOG.debug("Could not load theme prefs")