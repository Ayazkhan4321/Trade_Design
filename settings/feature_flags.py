"""Feature flags sourced from environment variables.

Keep feature toggles (boolean flags) here so they can be overridden in
tests or deployments without touching API endpoint configuration.
"""
import os

ALLOW_EXPLICIT_USER_MESSAGES = str(os.getenv("ALLOW_EXPLICIT_USER_MESSAGES", "0")).lower() in ("1", "true")
