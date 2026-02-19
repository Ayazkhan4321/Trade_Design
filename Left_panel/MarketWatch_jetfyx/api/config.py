"""Thin compatibility wrapper for MarketWatch_jetfyx to expose API and hub
configuration used by the MarketWatch services.

This module re-exports the canonical API config and ensures `HUB_BASE_URL`
is present (derived from `API_BASE_URL`) so imports like
`from MarketWatch_jetfyx.api.config import HUB_BASE_URL` succeed.
"""

# Prefer the centralized accounts API config which already exposes the hub URL
from accounts.api.config import *  # noqa: F401,F403

import re

# Some callers import `HUB_BASE_URL` directly from this module. If the
# re-export above didn't provide it (older setups), derive it from
# `API_BASE_URL` as a fallback.
try:
	HUB_BASE_URL  # type: ignore
except NameError:
	HUB_BASE_URL = re.sub(r"/api/?$", "", API_BASE_URL, flags=re.IGNORECASE)

__all__ = [name for name in globals().keys() if not name.startswith("_")]



