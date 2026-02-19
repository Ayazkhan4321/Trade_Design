"""Compatibility wrapper: reuse the centralized login dialog from `accounts`.

MarketWatch previously contained a full copy of the login dialog. To avoid
duplication keep a small compatibility module that re-exports the canonical
`LoginPage` from `accounts`.
"""
"""Compatibility wrapper: reuse the centralized login dialog from `Login`.

MarketWatch previously contained a full copy of the login dialog. To avoid
duplication keep a small compatibility module that re-exports the canonical
`LoginPage` from `Login.login_page`.
"""
from Login.login_page import LoginPage

__all__ = ["LoginPage"]
