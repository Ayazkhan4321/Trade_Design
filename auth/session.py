"""Convenience wrapper around auth_service for UI/session operations.

Keep sign-in/out logic in a single place for clearer separation of concerns.
"""
from typing import Optional

import auth.auth_service as auth_service


def get_current_user() -> Optional[str]:
    return auth_service.get_current_user()


def get_token() -> Optional[str]:
    return auth_service.get_token()


def is_signed_in() -> bool:
    return get_token() is not None


def sign_out() -> None:
    """Clear any stored session/token information."""
    auth_service.clear_token()
