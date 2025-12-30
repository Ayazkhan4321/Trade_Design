"""Styling utilities for Login page (separate file to avoid collisions).

Provides hover behavior for `lbl_forgot_password` so the label turns red on hover
and shows a pointer cursor.
"""
from PySide6.QtCore import Qt


def apply_login_styles(ui):
    try:
        ui.lbl_forgot_password.setStyleSheet(
            "QLabel#lbl_forgot_password{ color: #1976D2; }"
            "QLabel#lbl_forgot_password:hover{ color: #d32f2f; cursor: pointer; }"
        )
        # ensure cursor is pointer initially to indicate clickability
        ui.lbl_forgot_password.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    try:
        ui.lbl_create_account.setStyleSheet(
            "QLabel#lbl_create_account{ color: #1976D2; }"
            "QLabel#lbl_create_account:hover{ color: #d32f2f; cursor: pointer; }"
        )
        # ensure cursor is pointer initially to indicate clickability
        ui.lbl_create_account.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass
