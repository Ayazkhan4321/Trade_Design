"""Styling for Create Account - Step 1 (Personal Information).

Handles styling for the first page with name, email, phone, and referral code fields.
"""
from typing import Optional
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont


def _ensure_resources():
    """Ensure resource files are imported."""
    try:
        import Main_Icons_rc
    except Exception:
        try:
            from Icons import Main_Icons_rc as Main_Icons_rc
        except Exception:
            Main_Icons_rc = None
    return True


def apply_step1_styles(ui, parent_dialog: Optional[object] = None) -> None:
    """Apply styling for Step 1 - Personal Information page.
    
    This includes:
    - Title and tagline styling
    - Form input fields (First Name, Last Name, Email, Phone, Referral Code)
    - Country code dropdown
    - Continue button
    - Sign-in link
    - Logo display
    """
    _ensure_resources()

    # ========== FONTS ==========
    try:
        # Base font for the entire widget
        base_font = QFont()
        base_font.setFamily("Segoe UI")
        base_font.setPointSize(10)
        ui.widget.setFont(base_font)
    except Exception:
        pass

    # ========== LOGO ==========
    try:
        primary = ':/Main_Window/Icons/smallest_logo.png'
        pix = QPixmap(primary)
        if pix.isNull():
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            disk_path = os.path.join(repo_root, 'Icons', 'smallest_logo.png')
            if os.path.exists(disk_path):
                pix = QPixmap(disk_path)
        if not pix.isNull() and hasattr(ui, 'lb_logo_2'):
            ui.lb_logo_2.setPixmap(pix)
            ui.lb_logo_2.setFixedSize(50, 50)
            ui.lb_logo_2.setScaledContents(True)
    except Exception:
        pass

    # ========== TITLE & TAGLINE ==========
    try:
        ui.lb_title_2.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-weight: 700;
                font-size: 28pt;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
    except Exception:
        pass

    try:
        ui.lb_tagline_2.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-size: 11pt;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 0px;
                margin-bottom: 12px;
            }
        """)
    except Exception:
        pass

    # ========== STEP INDICATORS ==========
    # Step indicator ball style
    step_active_style = """
        QLabel {
            background-color: #d32f2f;
            color: white;
            font-weight: 700;
            font-size: 12pt;
            border-radius: 18px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }
    """
    
    step_inactive_style = """
        QLabel {
            background-color: #757575;
            color: white;
            font-weight: 600;
            font-size: 12pt;
            border-radius: 18px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }
    """
    
    try:
        # Step 1 (Active - Red) - lb_one_2
        if hasattr(ui, 'lb_one_2'):
            ui.lb_one_2.setStyleSheet(step_active_style)
            ui.lb_one_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif hasattr(ui, 'lb_step1_2'):
            ui.lb_step1_2.setStyleSheet(step_active_style)
            ui.lb_step1_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step 2 (Inactive - Gray) - lb_3
        if hasattr(ui, 'lb_3'):
            ui.lb_3.setStyleSheet(step_inactive_style)
            ui.lb_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_3.setText("2")
        elif hasattr(ui, 'lb_step2_2'):
            ui.lb_step2_2.setStyleSheet(step_inactive_style)
            ui.lb_step2_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step 3 (Inactive - Gray) - lb_4
        if hasattr(ui, 'lb_4'):
            ui.lb_4.setStyleSheet(step_inactive_style)
            ui.lb_4.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_4.setText("3")
        elif hasattr(ui, 'lb_step3_2'):
            ui.lb_step3_2.setStyleSheet(step_inactive_style)
            ui.lb_step3_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step connectors (lines between circles)
        if hasattr(ui, 'line_step1_2'):
            ui.line_step1_2.setStyleSheet("""
                QFrame {
                    background-color: #bdbdbd;
                    min-height: 3px;
                    max-height: 3px;
                }
            """)
        if hasattr(ui, 'line_step2_2'):
            ui.line_step2_2.setStyleSheet("""
                QFrame {
                    background-color: #bdbdbd;
                    min-height: 3px;
                    max-height: 3px;
                }
            """)
    except Exception:
        pass

    # ========== FORM FIELDS ==========
    # Common styling for all input fields
    input_field_style = """
        QLineEdit {
            padding: 8px 12px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            background-color: white;
            font-size: 10pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #424242;
        }
        QLineEdit:focus {
            border: 2px solid #d32f2f;
            background-color: #fafafa;
        }
        QLineEdit:hover {
            border: 1px solid #bdbdbd;
        }
        QLineEdit::placeholder {
            color: #9e9e9e;
        }
    """

    try:
        # First Name field
        ui.le_first_name.setStyleSheet(input_field_style)
        ui.le_first_name.setPlaceholderText("First Name")
    except Exception:
        pass

    try:
        # Last Name field
        ui.le_last_name.setStyleSheet(input_field_style)
        ui.le_last_name.setPlaceholderText("Last Name")
    except Exception:
        pass

    try:
        # Email field - using le_email (not le_email_address)
        if hasattr(ui, 'le_email'):
            ui.le_email.setStyleSheet(input_field_style)
            ui.le_email.setPlaceholderText("Email")
        elif hasattr(ui, 'le_email_address'):
            ui.le_email_address.setStyleSheet(input_field_style)
            ui.le_email_address.setPlaceholderText("Email Address")
    except Exception:
        pass

    try:
        # Phone Number field
        ui.le_number.setStyleSheet(input_field_style)
        ui.le_number.setPlaceholderText("Phone Number")
    except Exception:
        pass

    try:
        # Referral Code field
        ui.le_refferal_code.setStyleSheet(input_field_style)
        ui.le_refferal_code.setPlaceholderText("Referral Code")
    except Exception:
        pass

    # ========== COUNTRY CODE DROPDOWN ==========
    try:
        ui.cmb_country_code.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 10pt;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #424242;
            }
            QComboBox:focus {
                border: 2px solid #d32f2f;
            }
            QComboBox:hover {
                border: 1px solid #bdbdbd;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border-left: 1px solid #e0e0e0;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                background-color: white;
                selection-background-color: #ffebee;
                selection-color: #d32f2f;
                padding: 4px;
            }
        """)
    except Exception:
        pass

    # ========== ERROR/VALIDATION LABELS ==========
    try:
        # First name error label
        if hasattr(ui, 'lb_first_name_err'):
            ui.lb_first_name_err.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 8pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding-left: 4px;
                }
            """)
    except Exception:
        pass

    # ========== CONTINUE BUTTON ==========
    button_style = """
        QPushButton {
            background-color: #d32f2f;
            color: white;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            text-align: center;
        }
        QPushButton:hover {
            background-color: #c62828;
        }
        QPushButton:pressed {
            background-color: #b71c1c;
        }
        QPushButton:disabled {
            background-color: #e0e0e0;
            color: #9e9e9e;
        }
    """
    
    try:
        # Try different button names
        if hasattr(ui, 'pb_continue_to_account_selection'):
            ui.pb_continue_to_account_selection.setStyleSheet(button_style)
            ui.pb_continue_to_account_selection.setCursor(Qt.PointingHandCursor)
        elif hasattr(ui, 'pb_continue_verify'):
            ui.pb_continue_verify.setStyleSheet(button_style)
            ui.pb_continue_verify.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    # ========== SIGN IN LINK ==========
    try:
        ui.lb_signin.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-size: 10pt;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        ui.lb_signin.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    try:
        # "Already have an account?" text
        if hasattr(ui, 'lb_have_account'):
            ui.lb_have_account.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-size: 10pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
    except Exception:
        pass

    # ========== MAIN WIDGET BACKGROUND ==========
    try:
        ui.widget.setStyleSheet("""
            QWidget#widget {
                background-color: white;
                border: 3px solid #d32f2f;
                border-radius: 16px;
            }
        """)
    except Exception:
        pass
