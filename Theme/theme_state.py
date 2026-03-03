"""
theme_state.py  –  Single source of truth for all colour tokens.

Supported themes:
  dark | light | crazy_red | crazy_green | crazy_purple |
  crazy_orange | crazy_yellow | crazy_blue | time | system

Crazy themes use the LIGHT base palette with vivid accent overrides.
"""
from __future__ import annotations
import datetime
from typing import Dict, Any

CRAZY_COLORS: list[str] = ["red", "green", "purple", "orange", "yellow", "blue"]

TIME_PERIODS: Dict[str, Dict[str, Any]] = {
    "morning":   {"icon": "☀️",  "label": "Morning",   "start": "06:00", "end": "12:00", "sub_theme": "light"},
    "afternoon": {"icon": "🌤",  "label": "Afternoon",  "start": "12:00", "end": "18:00", "sub_theme": "light"},
    "evening":   {"icon": "🌆",  "label": "Evening",   "start": "18:00", "end": "21:00", "sub_theme": "dark"},
    "night":     {"icon": "🌙",  "label": "Night",     "start": "21:00", "end": "06:00", "sub_theme": "dark"},
}


def _dark() -> Dict[str, str]:
    return {
        "bg_window":        "#1a1f2e",
        "bg_panel":         "#1e2433",
        "bg_widget":        "#252b3b",
        "bg_popup":         "#1e2433",
        "bg_input":         "#2d3448",
        "bg_header":        "#161b28",
        "bg_row_alt":       "#222840",
        "bg_row_hover":     "#2a3352",
        "bg_selected":      "#1565c0",
        "bg_tab_active":    "#2c3450",
        "bg_tab_inactive":  "transparent",
        "bg_button":        "#2d3448",
        "bg_button_hover":  "#3a4460",
        "bg_bottom_bar":    "#1a1f2e",
        "bg_toggle_on":     "#1976d2",
        "bg_toggle_off":    "#4a5568",
        "text_primary":     "#e8eaf6",
        "text_secondary":   "#9099b4",
        "text_muted":       "#5a6482",
        "text_selected":    "#ffffff",
        "text_header":      "#9099b4",
        "text_link":        "#64b5f6",
        "text_positive":    "#4caf50",
        "text_negative":    "#f44336",
        "text_tab_active":  "#90caf9",
        "text_tab_inactive":"#9099b4",
        "border_primary":   "#2d3448",
        "border_secondary": "#3a4460",
        "border_focus":     "#1976d2",
        "border_separator": "#2d3448",
        "accent":           "#1976d2",
        "accent_hover":     "#1565c0",
        "accent_text":      "#ffffff",
        "popup_border_radius": "12px",
        "popup_border":     "#2d3448",
        "scrollbar_bg":     "#252b3b",
        "scrollbar_handle": "#3a4460",
    }


def _light() -> Dict[str, str]:
    return {
        "bg_window":        "#f0f4f8",
        "bg_panel":         "#ffffff",
        "bg_widget":        "#ffffff",
        "bg_popup":         "#ffffff",
        "bg_input":         "#f5f7fa",
        "bg_header":        "#f5f7fa",
        "bg_row_alt":       "#f9fafb",
        "bg_row_hover":     "#e3f2fd",
        "bg_selected":      "#1565c0",
        "bg_tab_active":    "#e6f0ff",
        "bg_tab_inactive":  "transparent",
        "bg_button":        "#f0f4f8",
        "bg_button_hover":  "#e2e8f0",
        "bg_bottom_bar":    "#f9fafb",
        "bg_toggle_on":     "#1976d2",
        "bg_toggle_off":    "#d1d5db",
        "text_primary":     "#1a202c",
        "text_secondary":   "#4a5568",
        "text_muted":       "#9ca3af",
        "text_selected":    "#ffffff",
        "text_header":      "#6b7280",
        "text_link":        "#1976d2",
        "text_positive":    "#16a34a",
        "text_negative":    "#dc2626",
        "text_tab_active":  "#1976d2",
        "text_tab_inactive":"#6b7280",
        "border_primary":   "#e5e7eb",
        "border_secondary": "#d1d5db",
        "border_focus":     "#1976d2",
        "border_separator": "#e5e7eb",
        "accent":           "#1976d2",
        "accent_hover":     "#1565c0",
        "accent_text":      "#ffffff",
        "popup_border_radius": "12px",
        "popup_border":     "#e5e7eb",
        "scrollbar_bg":     "#f0f4f8",
        "scrollbar_handle": "#d1d5db",
    }


# Crazy accents applied ON TOP of LIGHT base — vivid colours pop on white bg
_CRAZY_ACCENTS: Dict[str, Dict[str, str]] = {
    "red": {
        "accent": "#e53935", "accent_hover": "#c62828",
        "bg_selected": "#c62828", "bg_tab_active": "#fce4e4",
        "bg_toggle_on": "#e53935", "text_tab_active": "#e53935",
        "border_focus": "#e53935", "text_link": "#e53935",
        "bg_header": "#fce4e4", "border_separator": "#f5c6c6",
        "border_primary": "#f5c6c6",
    },
    "green": {
        "accent": "#2e7d32", "accent_hover": "#1b5e20",
        "bg_selected": "#1b5e20", "bg_tab_active": "#e8f5e9",
        "bg_toggle_on": "#2e7d32", "text_tab_active": "#2e7d32",
        "border_focus": "#2e7d32", "text_link": "#2e7d32",
        "bg_header": "#e8f5e9", "border_separator": "#c8e6c9",
        "border_primary": "#c8e6c9",
    },
    "purple": {
        "accent": "#7c3aed", "accent_hover": "#5b21b6",
        "bg_selected": "#4a148c", "bg_tab_active": "#f3e5f5",
        "bg_toggle_on": "#7c3aed", "text_tab_active": "#7c3aed",
        "border_focus": "#7c3aed", "text_link": "#7c3aed",
        "bg_header": "#f3e5f5", "border_separator": "#e1bee7",
        "border_primary": "#e1bee7",
    },
    "orange": {
        "accent": "#f97316", "accent_hover": "#ea580c",
        "bg_selected": "#bf360c", "bg_tab_active": "#fff3e0",
        "bg_toggle_on": "#f97316", "text_tab_active": "#f97316",
        "border_focus": "#f97316", "text_link": "#f97316",
        "bg_header": "#fff3e0", "border_separator": "#ffccbc",
        "border_primary": "#ffccbc",
    },
    "yellow": {
        "accent": "#d97706", "accent_hover": "#b45309",
        "bg_selected": "#92400e", "bg_tab_active": "#fffde7",
        "bg_toggle_on": "#d97706", "text_tab_active": "#b45309",
        "border_focus": "#d97706", "text_link": "#b45309",
        "bg_header": "#fffde7", "border_separator": "#fef08a",
        "border_primary": "#fef08a",
    },
    "blue": {
        "accent": "#1d4ed8", "accent_hover": "#1e3a8a",
        "bg_selected": "#1e3a8a", "bg_tab_active": "#dbeafe",
        "bg_toggle_on": "#1d4ed8", "text_tab_active": "#1d4ed8",
        "border_focus": "#1d4ed8", "text_link": "#1d4ed8",
        "bg_header": "#dbeafe", "border_separator": "#bfdbfe",
        "border_primary": "#bfdbfe",
    },
}


def _is_system_dark() -> bool:
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            pal = app.palette()
            return pal.window().color().lightness() < 128
    except Exception:
        pass
    return False


def _resolve_time_sub() -> str:
    h = datetime.datetime.now().hour
    if 6 <= h < 12:  return TIME_PERIODS["morning"]["sub_theme"]
    if 12 <= h < 18: return TIME_PERIODS["afternoon"]["sub_theme"]
    if 18 <= h < 21: return TIME_PERIODS["evening"]["sub_theme"]
    return TIME_PERIODS["night"]["sub_theme"]


def get_active_time_period() -> str:
    h = datetime.datetime.now().hour
    if 6 <= h < 12:  return "morning"
    if 12 <= h < 18: return "afternoon"
    if 18 <= h < 21: return "evening"
    return "night"


def get_tokens(theme_name: str) -> Dict[str, str]:
    n = theme_name.lower().strip()
    if n == "light":  return _light()
    if n == "dark":   return _dark()
    if n == "system": return _dark() if _is_system_dark() else _light()
    if n == "time":   return get_tokens(_resolve_time_sub())
    if n.startswith("crazy_"):
        color = n[6:]
        base = _light()   # ← LIGHT base so swatch accent pops on white background
        base.update(_CRAZY_ACCENTS.get(color, _CRAZY_ACCENTS["red"]))
        return base
    return _dark()


def friendly_name(theme_name: str) -> str:
    m = {
        "dark": "Dark Mode", "light": "Light Mode", "system": "System Default",
        "crazy_red":    "Red Theme",    "crazy_green":  "Green Theme",
        "crazy_purple": "Purple Theme", "crazy_orange": "Orange Theme",
        "crazy_yellow": "Yellow Theme", "crazy_blue":   "Blue Theme",
        "time": "Time-Based Theme",
    }
    return m.get(theme_name.lower(), theme_name.title())