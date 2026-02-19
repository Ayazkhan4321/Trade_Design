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


from typing import Dict, Optional

EXPECTED_KEYS = ("name", "dial_code", "code")


def normalize_country_data(country: Dict) -> Optional[Dict]:
    """Normalize API country payload into a strict internal schema.

    API example:
    {
      "name": "Afghanistan",
      "code": "AF",
      "phoneCode": "+93"
    }
    """
    if not isinstance(country, dict):
        return None

    name = country.get("name")
    code = country.get("code")
    # Accept multiple possible input keys for phone code/dial_code used across
    # different API responses or fixtures: 'dial_code', 'dial', or 'phoneCode'.
    phone_code = country.get("dial_code") or country.get("dial") or country.get("phoneCode")

    if not name and not code:
        return None

    out = {
        "name": name,
        "code": code.upper() if isinstance(code, str) else None,
        "dial_code": phone_code if phone_code and str(phone_code).startswith("+")
        else f"+{phone_code}" if phone_code else None,
    }

    # Remove None values
    return {k: v for k, v in out.items() if v}



def country_has_valid_dial(country: Dict) -> bool:
    """Return True if the country dict contains a usable dial code."""
    if not isinstance(country, dict):
        return False
    dial = country.get("dial_code") or country.get("dial")
    return bool(dial)
