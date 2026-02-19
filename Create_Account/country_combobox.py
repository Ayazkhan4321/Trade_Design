"""Helpers to populate the country combo box with flag + dial code + name.

This keeps all combobox formatting logic in one place so the controller stays lean.
"""
from typing import List, Dict, Optional
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Qt
from .country_utils import normalize_country_data


def _code_to_flag_emoji(country_code: str) -> str:
    """Return the emoji flag for a 2-letter country code, or empty string."""
    if not country_code or not isinstance(country_code, str) or len(country_code) != 2:
        return ""
    base = 0x1F1E6  # Regional Indicator Symbol Letter A
    try:
        return chr(base + (ord(country_code.upper()[0]) - ord('A'))) + \
               chr(base + (ord(country_code.upper()[1]) - ord('A')))
    except Exception:
        return ""


def populate_country_combobox(combo: QComboBox, countries: List[Dict]) -> None:
    """Populate the given QComboBox with flag + dial code + name entries.

    - Collapsed display: flag + dial code
    - Dropdown list: flag + dial code + country name
    """
    combo.clear()
    combo.setEditable(True)
    try:
        combo.lineEdit().setReadOnly(True)
        combo.lineEdit().setPlaceholderText("Select country")
    except Exception:
        pass

    added = False
    max_text_width = 0
    font_metrics = combo.fontMetrics()
    for c in countries:
        normalized = normalize_country_data(c) if isinstance(c, dict) else None
        if normalized is None:
            continue
        name = normalized.get("name", "")
        dial = normalized.get("dial_code")
        code = normalized.get("code", "")
        flag = _code_to_flag_emoji(code)

        list_text = f"{flag} {dial} {name}".strip()
        minimal_text = f"{flag} {dial}".strip()
        data_payload = normalized

        idx = combo.count()
        combo.addItem(list_text, data_payload)
        # Store minimal text for line-edit display
        combo.setItemData(idx, minimal_text, Qt.UserRole + 1)
        max_text_width = max(max_text_width, font_metrics.horizontalAdvance(list_text))
        added = True

    if not added:
        # Fallback entry if no countries were added
        combo.addItem("Select country", None)
        return

    # When selection changes, show minimal text (flag + dial) in the line edit
    def _update_display(index: int) -> None:
        try:
            minimal = combo.itemData(index, Qt.UserRole + 1)
            if minimal is None:
                minimal = combo.itemText(index)
            combo.lineEdit().setText(minimal)
        except Exception:
            pass

    combo.currentIndexChanged.connect(_update_display)
    _update_display(combo.currentIndex())

    # Widen the popup to fit the longest entry (add padding)
    try:
        view = combo.view()
        padding = 32
        min_width = max_text_width + padding
        view.setMinimumWidth(min_width)
    except Exception:
        pass
