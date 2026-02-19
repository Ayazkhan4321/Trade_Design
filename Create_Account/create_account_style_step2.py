"""Styling for Create Account - Step 2 (Account Type Selection).

Handles styling for the second page where users select their account type.
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


def apply_step2_styles(ui, parent_dialog: Optional[object] = None) -> None:
    """Apply styling for Step 2 - Account Type Selection page.
    
    This includes:
    - Title and tagline styling
    - Step indicators (with step 2 active)
    - Account type selection tabs (Live/Demo)
    - Account type buttons (Classic, ECN, Premium, Other)
    - Terms & Privacy checkbox
    - Continue button
    """
    _ensure_resources()

    # ========== FONTS ==========
    try:
        base_font = QFont()
        base_font.setFamily("Segoe UI")
        base_font.setPointSize(10)
        if hasattr(ui, 'widget'):
            ui.widget.setFont(base_font)
        # Also try to apply to page element
        if hasattr(ui, 'page'):
            ui.page.setFont(base_font)
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
            if hasattr(ui, 'lb_logo'):
                ui.lb_logo.setPixmap(pix)
                ui.lb_logo.setFixedSize(50, 50)
                ui.lb_logo.setScaledContents(True)
            elif hasattr(ui, 'lb_logo_3'):
                ui.lb_logo_3.setPixmap(pix)
                ui.lb_logo_3.setFixedSize(50, 50)
                ui.lb_logo_3.setScaledContents(True)
    except Exception:
        pass

    # ========== TITLE & TAGLINE ==========
    try:
        # Try different title label names
        if hasattr(ui, 'lb_title'):
            ui.lb_title.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-weight: 700;
                    font-size: 28pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        elif hasattr(ui, 'lb_title_3'):
            ui.lb_title_3.setStyleSheet("""
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
        if hasattr(ui, 'lb_tagline'):
            ui.lb_tagline.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 11pt;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 12px;
                }
            """)
        elif hasattr(ui, 'lb_tagline_3'):
            ui.lb_tagline_3.setStyleSheet("""
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
    # Step indicator styles for page 2
    step_completed_style = """
        QLabel {
            background-color: #4caf50;
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
        # Step 1 (Completed - Green) - lb_one
        if hasattr(ui, 'lb_one'):
            ui.lb_one.setStyleSheet(step_completed_style)
            ui.lb_one.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif hasattr(ui, 'lb_one_3'):
            ui.lb_one_3.setStyleSheet(step_completed_style)
            ui.lb_one_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif hasattr(ui, 'lb_step1_3'):
            ui.lb_step1_3.setStyleSheet(step_completed_style)
            ui.lb_step1_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step 2 (Active - Red) - lb_2
        if hasattr(ui, 'lb_2'):
            ui.lb_2.setStyleSheet(step_active_style)
            ui.lb_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_2.setText("2")
        elif hasattr(ui, 'lb_5'):
            ui.lb_5.setStyleSheet(step_active_style)
            ui.lb_5.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_5.setText("2")
        elif hasattr(ui, 'lb_step2_3'):
            ui.lb_step2_3.setStyleSheet(step_active_style)
            ui.lb_step2_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step 3 (Inactive - Gray) - lb_7
        if hasattr(ui, 'lb_7'):
            ui.lb_7.setStyleSheet(step_inactive_style)
            ui.lb_7.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_7.setText("3")
        elif hasattr(ui, 'lb_6'):
            ui.lb_6.setStyleSheet(step_inactive_style)
            ui.lb_6.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui.lb_6.setText("3")
        elif hasattr(ui, 'lb_step3_3'):
            ui.lb_step3_3.setStyleSheet(step_inactive_style)
            ui.lb_step3_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
    except Exception:
        pass

    # ========== TAB WIDGET (LIVE/DEMO) ==========
    try:
        if hasattr(ui, 'Live_Demo_tab_2'):
            ui.Live_Demo_tab_2.setStyleSheet("""
                QTabWidget::pane {
                    border: none;
                    background-color: transparent;
                }
                QTabWidget::tab-bar {
                    alignment: left;
                }
                QTabBar::tab {
                    background-color: #f5f5f5;
                    color: #757575;
                    padding: 12px 32px;
                    border: 1px solid #e0e0e0;
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    min-width: 120px;
                    margin-right: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #d32f2f;
                    color: white;
                    border: 1px solid #d32f2f;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #eeeeee;
                }
            """)
        elif hasattr(ui, 'Live_Demo_tab'):
            ui.Live_Demo_tab.setStyleSheet("""
                QTabWidget::pane {
                    border: none;
                    background-color: transparent;
                }
                QTabWidget::tab-bar {
                    alignment: left;
                }
                QTabBar::tab {
                    background-color: #f5f5f5;
                    color: #757575;
                    padding: 12px 32px;
                    border: 1px solid #e0e0e0;
                    border-bottom: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    min-width: 120px;
                    margin-right: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #d32f2f;
                    color: white;
                    border: 1px solid #d32f2f;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #eeeeee;
                }
            """)
    except Exception:
        pass

    # ========== ACCOUNT TYPE BUTTONS ==========
    account_button_style = """
        QPushButton {
            background-color: white;
            color: #424242;
            font-size: 10pt;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 10px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
        }
        QPushButton:hover {
            border: 2px solid #d32f2f;
            background-color: #ffebee;
        }
        QPushButton:pressed {
            background-color: #ffcdd2;
        }
        QPushButton:checked {
            background-color: white;
            color: #d32f2f;
            border: 2px solid #d32f2f;
            font-weight: 700;
        }
    """

    # Apply to all button name variations (Live and Demo tabs)
    button_names = ['pb_classic_3', 'pb_ecn_3', 'pb_premium_3', 'pb_other_3',
                    'pb_classic', 'pb_ecn', 'pb_premium', 'pb_other',
                    # Demo tab buttons
                    'pb_demo_2', 'pb_new_grp', 'pb_demo_grp']
    
    for btn_name in button_names:
        try:
            if hasattr(ui, btn_name):
                btn = getattr(ui, btn_name)
                btn.setStyleSheet(account_button_style)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setCheckable(True)
        except Exception:
            pass
    
    # Also ensure demo tab labels are styled properly
    try:
        if hasattr(ui, 'lb_live_2'):
            ui.lb_live_2.setStyleSheet("""
                QLabel {
                    color: #424242;
                    font-size: 10pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
    except Exception:
        pass
    
    try:
        if hasattr(ui, 'ld_demo_2'):
            ui.ld_demo_2.setStyleSheet("""
                QLabel {
                    color: #424242;
                    font-size: 10pt;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
    except Exception:
        pass

    # ========== TERMS & PRIVACY CHECKBOX ==========
    try:
        if hasattr(ui, 'cb_terms_privacy_policy'):
            cb = ui.cb_terms_privacy_policy
            cb.setTextFormat(Qt.RichText)
            cb.setTextInteractionFlags(Qt.TextBrowserInteraction)
            cb.setOpenExternalLinks(True)
            cb.setText(
                'I agree to the '
                '<a href="https://example.com/terms" style="color:#d32f2f; text-decoration: underline;">Terms of Service</a>'
                ' and '
                '<a href="https://example.com/privacy" style="color:#d32f2f; text-decoration: underline;">Privacy Policy</a>'
            )
            cb.setStyleSheet("""
                QCheckBox {
                    color: #424242;
                    font-size: 9pt;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #e0e0e0;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #d32f2f;
                }
                QCheckBox::indicator:checked {
                    background-color: #d32f2f;
                    border: 2px solid #d32f2f;
                    image: url(:/icons/check-white.png);
                }
            """)
    except Exception:
        pass

    # ========== CONTINUE BUTTON ==========
    continue_button_style = """
        QPushButton {
            background-color: #d32f2f;
            color: white;
            font-size: 10pt;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 6px 20px;
            border: none;
            border-radius: 6px;
            text-align: center;
            min-height: 32px;
            max-height: 36px;
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
        if hasattr(ui, 'pb_continue_to_verification'):
            ui.pb_continue_to_verification.setStyleSheet(continue_button_style)
            ui.pb_continue_to_verification.setCursor(Qt.PointingHandCursor)
            # Ensure text is set properly
            try:
                ui.pb_continue_to_verification.setText("Continue & Send Verification Code")
            except Exception:
                pass
    except Exception:
        pass

    # ========== BACK BUTTON ==========
    back_button_style = """
        QPushButton {
            background-color: #ffcdd2;
            color: #d32f2f;
            font-size: 10pt;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 6px 20px;
            border: none;
            border-radius: 6px;
            text-align: center;
            min-height: 32px;
            max-height: 36px;
        }
        QPushButton:hover {
            background-color: #ffb3ba;
        }
        QPushButton:pressed {
            background-color: #ff9aa2;
        }
    """
    
    try:
        if hasattr(ui, 'pb_back_2'):
            ui.pb_back_2.setStyleSheet(back_button_style)
            ui.pb_back_2.setCursor(Qt.PointingHandCursor)
            # Ensure text is set properly
            try:
                ui.pb_back_2.setText("← Back to Registration")
            except Exception:
                pass
        elif hasattr(ui, 'pb_back'):
            ui.pb_back.setStyleSheet(back_button_style)
            ui.pb_back.setCursor(Qt.PointingHandCursor)
            try:
                ui.pb_back.setText("← Back to Registration")
            except Exception:
                pass
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
