"""Styling utilities for the Forgot Password UI.

Keep all runtime styling (colors, icon sizing, cursors, spacing) here so the
generated `forgot_password_ui.py` remains untouched and can be re-generated
from Qt Designer without losing customizations.
"""
from typing import Optional
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def _ensure_resources():
    # Ensure compiled Main_Icons resource is registered (preferred).
    # We intentionally avoid legacy mail_icon fallbacks and rely on the 'Main_Icons.qrc' asset
    try:
        import Main_Icons_rc  # compiled qrc in repo root
    except Exception:
        try:
            from Icons import Main_Icons_rc as Main_Icons_rc  # fallback location
        except Exception:
            Main_Icons_rc = None
    return True


def apply_forgot_password_styles(ui, parent_dialog: Optional[object] = None) -> None:
    """Apply styling to the generated UI elements.

    Args:
        ui: instance of `Ui_Forgot_Password` (the generated UI bindings)
        parent_dialog: optional dialog instance; provided for future uses
    """
    _ensure_resources()

    # Title styling: red and slightly bolder for emphasis
    try:
        ui.lb_title_reset_password.setStyleSheet("color: #d32f2f; font-weight: 600;")
    except Exception:
        pass

    # Remove extra top margin so the description sits close to the title
    try:
        # Use stylesheet margin to avoid manipulating layouts (keeps generated file safe)
        ui.lb_desc_line_forgot_pass.setStyleSheet("margin-top:0px;")
    except Exception:
        pass

    # Icon handling: prefer the Main_Icons.qrc resource and fall back to disk if necessary
    try:
        primary = ':/Main_Window/Icons/mail.png'
        pix = QPixmap(primary)
        if pix.isNull():
            # If resource not available at runtime, try a disk fallback (project Icons/mail.png)
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            disk_path = os.path.join(repo_root, 'Icons', 'mail.png')
            if os.path.exists(disk_path):
                pix = QPixmap(disk_path)
        if not pix.isNull():
            ui.lb_forgot_password.setPixmap(pix)
            ui.lb_forgot_password.setFixedSize(24, 24)
            ui.lb_forgot_password.setScaledContents(True)
            ui.lb_forgot_password.setAlignment(Qt.AlignCenter)
    except Exception:
        pass

    # Send button: red appearance, disabled uses gray
    try:
        ui.pb_send_link.setStyleSheet(
            "QPushButton{ background-color:#d32f2f; color:white; padding:6px 12px; border-radius:4px;}"
            "QPushButton:disabled{ background-color:#bdbdbd; color:#6d6d6d;}"
        )
        ui.pb_send_link.setCursor(Qt.ForbiddenCursor)
    except Exception:
        pass

    try:
        ui.pb_cancel.setStyleSheet(
            "QPushButton{ background-color:white; padding:6px 12px; border-radius:4px;}"
            #"QPushButton:disabled{ background-color:#bdbdbd; color:#6d6d6d;}"
        )
        #ui.pb_send_link.setCursor(Qt.ForbiddenCursor)
    except Exception:
        pass

    # Provide a subtle default styling for the input; controller will toggle red border
    try:
        ui.le_forgot_password.setStyleSheet(
            "QLineEdit{ padding:6px; border:1px solid #cfcfcf; border-radius:3px;}"
            "QLineEdit:focus{ border:1px solid #1976D2; }"
        )
    except Exception:
        pass
