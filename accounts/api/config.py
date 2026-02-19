"""Thin wrapper that re-exports the canonical API configuration.

Keep this module so imports using `accounts.api.config` continue to work
while centralizing all constants in `api.config`.
"""

from api.config import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith("_")]
