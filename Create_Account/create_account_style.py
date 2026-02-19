"""Styling utilities for the Create Account UI.

Keeps all runtime styling separate from the generated `create_account_ui.py` file.
"""
from typing import Optional
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont


def _ensure_resources():
    try:
        import Main_Icons_rc
    except Exception:
        try:
            from Icons import Main_Icons_rc as Main_Icons_rc
        except Exception:
            Main_Icons_rc = None
    return True


def apply_create_account_styles(ui, parent_dialog: Optional[object] = None) -> None:
    """Apply an enhanced style that better matches Qt Designer defaults.

    This function focuses on font sizing, spacing, and consistent button/input
    appearance without modifying the generated UI layout.
    """
    _ensure_resources()

    # Base font for the dialog (use system default while nudging size)
    try:
        base_font = QFont()
        base_font.setPointSize(10)
        # apply to top-level widgets if possible
        ui.widget.setFont(base_font)
    except Exception:
        pass

    # Title and tagline
    try:
        ui.lb_title.setStyleSheet("color: #d32f2f; font-weight: 600; font-size: 16pt;")
        ui.lb_tagline.setStyleSheet("color: #9e9e9e; font-size: 9pt; margin-bottom:6px;")
    except Exception:
        pass

    # Form field default styling (consistent padding and focus outline)
    field_qss = (
        "QLineEdit, QComboBox { padding:6px; border:1px solid #cfcfcf; border-radius:4px; }"
        "QLineEdit:focus, QComboBox:focus { border:1px solid #1976D2; }"
        "QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; }")
    try:
        ui.le_first_name.setStyleSheet(field_qss)
        ui.le_last_name.setStyleSheet(field_qss)
        ui.le_number.setStyleSheet(field_qss)
        ui.le_refferal_code.setStyleSheet(field_qss)
        ui.cmb_country_code.setStyleSheet(field_qss)
    except Exception:
        pass

    # Primary action button styling
    try:
        ui.pb_continue_verify.setStyleSheet(
            "QPushButton{ background-color:#d32f2f; color:white; padding:8px 16px; border-radius:4px; font-weight:600; }"
            "QPushButton:hover{ background-color:#b71c1c; }"
            "QPushButton:disabled{ background-color:#bdbdbd; color:#6d6d6d; }"
        )
        ui.pb_continue_verify.setCursor(Qt.ForbiddenCursor)
        ui.pb_continue_verify.setMinimumHeight(36)
    except Exception:
        pass

    # Account type toggle buttons: use consistent sizing and spacing
    try:
        for btn_name in ("pb_classic", "pb_ecn", "pb_premium", "pb_other"):
            btn = getattr(ui, btn_name, None)
            if btn is not None:
                btn.setStyleSheet("QPushButton{ padding:6px 12px; border-radius:4px; }")
    except Exception:
        pass

    # Sign-in label should look like a link
    try:
        ui.lb_signin.setStyleSheet("color:#1976D2; text-decoration: underline; cursor: pointer;")
    except Exception:
        pass

    # Make Terms/Privacy text two separate links on the checkbox
    try:
        cb = ui.cb_terms_privacy_policy
        cb.setTextFormat(Qt.RichText)
        cb.setTextInteractionFlags(Qt.TextBrowserInteraction)
        cb.setOpenExternalLinks(True)
        cb.setText(
            'I agree to the '
            '<a href="https://example.com/terms" style="color:#1976D2; text-decoration: underline;">Terms of Service</a>'
            ' and '
            '<a href="https://example.com/privacy" style="color:#1976D2; text-decoration: underline;">Privacy Policy</a>'
        )
        cb.setStyleSheet("QCheckBox { color:#4a4a4a; } QCheckBox::indicator { margin-right:6px; }")
    except Exception:
        pass

    # Tab widget sizing to avoid tight contents
    try:
        ui.Live_Demo_tab.setStyleSheet("QTabWidget::pane { padding: 6px; }")
    except Exception:
        pass

    # Small icon handling: if resources are available, keep them aligned
    try:
        primary = ':/Main_Window/Icons/smallest_logo.png'
        pix = QPixmap(primary)
        if pix.isNull():
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            disk_path = os.path.join(repo_root, 'Icons', 'smallest_logo.png')
            if os.path.exists(disk_path):
                pix = QPixmap(disk_path)
        if not pix.isNull() and hasattr(ui, 'lb_logo'):
            ui.lb_logo.setPixmap(pix)
            ui.lb_logo.setFixedSize(32, 32)
            ui.lb_logo.setScaledContents(True)
    except Exception:
        pass

    # Keep small tweaks separate from generated UI. Additional adjustments can
    # be made per-project or replaced with a single global stylesheet if desired.

