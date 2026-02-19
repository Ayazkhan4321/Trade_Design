"""Styling for Create Account - Step 3 (OTP Verification).

Handles styling for the third page where users enter and verify their OTP code.
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


def apply_step3_styles(ui, parent_dialog: Optional[object] = None) -> None:
    """Apply styling for Step 3 - OTP Verification page.
    
    This includes:
    - Title and tagline styling
    - Step indicators (with step 3 active)
    - OTP code input field
    - Verify button
    - Resend OTP option
    - Timer/countdown display
    """
    _ensure_resources()

    # ========== FONTS ==========
    try:
        base_font = QFont()
        base_font.setFamily("Segoe UI")
        base_font.setPointSize(10)
        if hasattr(ui, 'widget'):
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
        if not pix.isNull():
            if hasattr(ui, 'lb_logo_4'):
                ui.lb_logo_4.setPixmap(pix)
                ui.lb_logo_4.setFixedSize(50, 50)
                ui.lb_logo_4.setScaledContents(True)
            elif hasattr(ui, 'lb_logo'):
                ui.lb_logo.setPixmap(pix)
                ui.lb_logo.setFixedSize(50, 50)
                ui.lb_logo.setScaledContents(True)
    except Exception:
        pass

    # ========== TITLE & TAGLINE ==========
    try:
        if hasattr(ui, 'lb_title_4'):
            ui.lb_title_4.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-weight: 700;
                    font-size: 28pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        elif hasattr(ui, 'lb_title'):
            ui.lb_title.setStyleSheet("""
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
        if hasattr(ui, 'lb_tagline_4'):
            ui.lb_tagline_4.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 11pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 12px;
                }
            """)
        elif hasattr(ui, 'lb_tagline'):
            ui.lb_tagline.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 11pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 12px;
                }
            """)
    except Exception:
        pass

    # ========== STEP INDICATORS ==========
    # Step indicators on page 3: lb_one_4 (step 1), lb_8 (step 2), lb_9 (step 3)
    
    # Circular style for step indicators
    step_completed_style = """
        QLabel {
            background-color: #4caf50;
            color: white;
            font-weight: 700;
            font-size: 13pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            border-radius: 18px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }
    """
    
    step_active_style = """
        QLabel {
            background-color: #d32f2f;
            color: white;
            font-weight: 700;
            font-size: 13pt;
            font-family: 'Segoe UI', Arial, sans-serif;
            border-radius: 18px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }
    """
    
    try:
        # Step 1 - Completed (Green)
        for lb_name in ['lb_one_4', 'lb_step1_4']:
            if hasattr(ui, lb_name):
                lb = getattr(ui, lb_name)
                lb.setStyleSheet(step_completed_style)
                lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lb.setText("1")
        
        # Step 2 - Completed (Green)
        for lb_name in ['lb_8', 'lb_step2_4']:
            if hasattr(ui, lb_name):
                lb = getattr(ui, lb_name)
                lb.setStyleSheet(step_completed_style)
                lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lb.setText("2")
        
        # Step 3 - Active (Red)
        for lb_name in ['lb_9', 'lb_step3_4']:
            if hasattr(ui, lb_name):
                lb = getattr(ui, lb_name)
                lb.setStyleSheet(step_active_style)
                lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lb.setText("3")
    except Exception:
        pass

    # ========== MAIN HEADING ==========
    try:
        # "Verify Your Email" heading
        if hasattr(ui, 'lb_title_line_3'):
            ui.lb_title_line_3.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 18pt;
                    font-weight: 700;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-top: 16px;
                    margin-bottom: 8px;
                }
            """)
            ui.lb_title_line_3.setText("Verify Your Email")
            ui.lb_title_line_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
    except Exception:
        pass

    # ========== INSTRUCTION TEXT ==========
    try:
        if hasattr(ui, 'lb_otp_instruction'):
            ui.lb_otp_instruction.setStyleSheet("""
                QLabel {
                    color: #424242;
                    font-size: 10pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 16px;
                }
            """)
    except Exception:
        pass

    # ========== OTP INPUT FIELD ==========
    try:
        if hasattr(ui, 'le_code'):
            ui.le_code.setStyleSheet("""
                QLineEdit {
                    padding: 10px 16px;
                    border: 2px solid #d32f2f;
                    border-radius: 6px;
                    background-color: white;
                    font-size: 12pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #424242;
                }
                QLineEdit:focus {
                    border: 2px solid #d32f2f;
                    background-color: #fafafa;
                }
                QLineEdit:hover {
                    border: 2px solid #c62828;
                }
                QLineEdit::placeholder {
                    color: #9e9e9e;
                }
            """)
            ui.le_code.setPlaceholderText("Enter your code")
            ui.le_code.setMaxLength(6)
        elif hasattr(ui, 'le_otp_code'):
            ui.le_otp_code.setStyleSheet("""
                QLineEdit {
                    padding: 10px 16px;
                    border: 2px solid #d32f2f;
                    border-radius: 6px;
                    background-color: white;
                    font-size: 12pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #424242;
                }
                QLineEdit:focus {
                    border: 2px solid #d32f2f;
                    background-color: #fafafa;
                }
                QLineEdit:hover {
                    border: 2px solid #c62828;
                }
                QLineEdit::placeholder {
                    color: #9e9e9e;
                }
            """)
            ui.le_otp_code.setPlaceholderText("Enter your code")
            ui.le_otp_code.setMaxLength(6)
    except Exception:
        pass

    # ========== TIMER/COUNTDOWN DISPLAY ==========
    try:
        if hasattr(ui, 'lb_timer'):
            ui.lb_timer.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-size: 9pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-top: 8px;
                }
            """)
    except Exception:
        pass

    try:
        if hasattr(ui, 'lb_timer_warning'):
            ui.lb_timer_warning.setStyleSheet("""
                QLabel {
                    color: #ff6f00;
                    font-size: 9pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-top: 8px;
                }
            """)
    except Exception:
        pass

    # ========== RESEND OTP LINK ==========
    try:
        if hasattr(ui, 'lb_resend_otp'):
            ui.lb_resend_otp.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 10pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            ui.lb_resend_otp.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    try:
        if hasattr(ui, 'lb_resend_text'):
            ui.lb_resend_text.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-size: 10pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
    except Exception:
        pass

    # ========== VERIFY BUTTON ==========
    try:
        if hasattr(ui, 'pb_verify'):
            ui.pb_verify.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 8px 24px;
                    border: none;
                    border-radius: 8px;
                    min-height: 40px;
                    max-height: 44px;
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
            """)
            ui.pb_verify.setCursor(Qt.PointingHandCursor)
            ui.pb_verify.setText("✓ Verify & Continue to Login")
        elif hasattr(ui, 'pb_verify_otp'):
            ui.pb_verify_otp.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 8px 24px;
                    border: none;
                    border-radius: 8px;
                    min-height: 40px;
                    max-height: 44px;
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
            """)
            ui.pb_verify_otp.setCursor(Qt.PointingHandCursor)
            ui.pb_verify_otp.setText("✓ Verify & Continue to Login")
    except Exception:
        pass

    # ========== BACK BUTTON (if present) ==========
    try:
        if hasattr(ui, 'pb_back'):
            ui.pb_back.setStyleSheet("""
                QPushButton {
                    background-color: #ffcdd2;
                    color: #d32f2f;
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 8px 24px;
                    border: none;
                    border-radius: 8px;
                    min-height: 40px;
                    max-height: 44px;
                }
                QPushButton:hover {
                    background-color: #ffb3ba;
                }
                QPushButton:pressed {
                    background-color: #ff9aa2;
                }
            """)
            ui.pb_back.setCursor(Qt.PointingHandCursor)
            ui.pb_back.setText("← Back to Registration")
    except Exception:
        pass

    # ========== ERROR MESSAGE LABEL ==========
    try:
        if hasattr(ui, 'lb_otp_error'):
            ui.lb_otp_error.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 9pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 8px;
                    background-color: #ffebee;
                    border-radius: 4px;
                    border-left: 3px solid #d32f2f;
                }
            """)
    except Exception:
        pass

    # ========== SUCCESS MESSAGE LABEL ==========
    try:
        if hasattr(ui, 'lb_otp_success'):
            ui.lb_otp_success.setStyleSheet("""
                QLabel {
                    color: #2e7d32;
                    font-size: 9pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    padding: 8px;
                    background-color: #e8f5e9;
                    border-radius: 4px;
                    border-left: 3px solid #2e7d32;
                }
            """)
    except Exception:
        pass

    # ========== MAIN WIDGET BACKGROUND ==========
    try:
        if hasattr(ui, 'widget'):
            ui.widget.setStyleSheet("""
                QWidget#widget {
                    background-color: white;
                    border: 3px solid #d32f2f;
                    border-radius: 16px;
                }
            """)
    except Exception:
        pass
