"""Utilities for formatting and validating country data for the Create Account UI.

Keeps country-specific logic separate so it can be thoroughly unit-tested and
extended for production needs (e.g., strict schema validation, caching).
"""
from typing import Dict, Optional


EXPECTED_KEYS = ("name", "dial_code", "code")


def format_country_display(country: Dict) -> str:
    """Return a user-facing display string for the country combo box entry.

    Prefer showing dial code and name when available, otherwise fall back to name.
    """
    if not isinstance(country, dict):
        return str(country)
    name = country.get("name") or country.get("caption") or country.get("display") or ""
    dial = country.get("dial_code") or country.get("dial") or None
    if dial:
        return f"{dial} {name}"
    return name or ""


def normalize_country_data(country: Dict) -> Optional[Dict]:
    """Return a sanitized country dict with only allowed keys, or None if invalid.

    This helps guard against unexpected API responses at runtime and keeps the
    UI code simpler.
    """
    if not isinstance(country, dict):
        return None
    out = {}
    for k in EXPECTED_KEYS:
        if k in country and country[k] is not None:
            out[k] = country[k]
    # require at least a name or code
    if "name" not in out and "code" not in out:
        return None
    return out


def country_has_valid_dial(country: Dict) -> bool:
    """Return True if the country dict contains a usable dial code."""
    if not isinstance(country, dict):
        return False
    dial = country.get("dial_code") or country.get("dial")
    return bool(dial)
