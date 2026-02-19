"""Compatibility wrapper: re-export the canonical `LoginPage` from `Login`.

This keeps code that imports `Left_panel.accounts.login_page.LoginPage` working
while centralizing the implementation under `Login/login_page.py`.
"""
from Login.login_page import LoginPage

__all__ = ["LoginPage"]
