"""Styling utilities for Login page (separate file to avoid collisions).

Provides hover behavior for labels and comprehensive styling for the login dialog.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLineEdit


def apply_dialog_border(dialog):
    """Apply styling to the dialog itself."""
    dialog.setStyleSheet("""
        QDialog {
            background-color: white;
        }
    """)


def apply_login_styles(ui):
    """Apply custom styles to login dialog elements."""
    
    # Style the Live/Demo toggle buttons with reduced height
    try:
        # Live button
        ui.btn_live.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #E53935;
                border: 2px solid #E53935;
                border-radius: 18px;
                padding: 8px 25px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
                max-height: 20px;
            }
            QPushButton:checked {
                background-color: #E53935;
                color: white;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
            QPushButton:checked:hover {
                background-color: #D32F2F;
            }
        """)
        
        # Demo button
        ui.btn_demo.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #E53935;
                border: 2px solid #E53935;
                border-radius: 18px;
                padding: 8px 25px;
                font-size: 14px;
                font-weight: bold;
                min-height: 2px;
                max-height: 20px;
            }
            QPushButton:checked {
                background-color: #E53935;
                color: white;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
            QPushButton:checked:hover {
                background-color: #D32F2F;
            }
        """)
    except Exception:
        pass
    
    # Style input fields without background icons
    try:
        input_style = """
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: #F5F5F5;
            }
            QLineEdit:focus {
                border: 2px solid #E53935;
                background-color: white;
            }
        """
        ui.input_email.setStyleSheet(input_style)
        ui.input_password.setStyleSheet(input_style)
    except Exception:
        pass
    
    # Style icon labels to be visible and red - simplified approach
    try:
        # Simple styling for icon labels
        icon_style = """
            QLabel {
                background-color: transparent;
                min-width: 24px;
                max-width: 24px;
                min-height: 20px;
                max-height: 20px;
            }
        """
        
        if hasattr(ui, 'icon_email'):
            ui.icon_email.setStyleSheet(icon_style)
            # Ensure icon is visible and properly sized
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import Qt
            pixmap = QPixmap(":/Main_Window/Icons/Login_to_trade.png")
            if not pixmap.isNull():
                ui.icon_email.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        if hasattr(ui, 'icon_password'):
            ui.icon_password.setStyleSheet(icon_style)
            # Ensure icon is visible and properly sized
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import Qt
            pixmap = QPixmap(":/Main_Window/Icons/password.png")
            if not pixmap.isNull():
                ui.icon_password.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                
        print(f"Icon email exists: {hasattr(ui, 'icon_email')}")
        print(f"Icon password exists: {hasattr(ui, 'icon_password')}")
    except Exception as e:
        print(f"Icon styling error: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # Style Sign In button with reduced height
    try:
        ui.btn_signin.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 15px;
                font-weight: bold;
                min-height: 20px;
                max-height: 20px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        # Add sign-in icon
        #ui.btn_signin.setText("→  Sign In")
    except Exception:
        pass
    
    # Style forgot password label - red with blue hover
    try:
        ui.lbl_forgot_password.setStyleSheet("""
            QLabel {
                color: #E53935;
                font-size: 12px;
            }
            QLabel:hover {
                color: #1976D2;
                text-decoration: underline;
            }
        """)
        ui.lbl_forgot_password.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    # Style create account label - red with blue hover
    try:
        ui.lbl_create_account.setStyleSheet("""
            QLabel {
                color: #E53935;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel:hover {
                color: #1976D2;
                text-decoration: underline;
            }
        """)
        ui.lbl_create_account.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass
    
    # Style checkbox
    try:
        ui.cb_remember_me.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #757575;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #E0E0E0;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #E53935;
                border-color: #E53935;
            }
        """)
    except Exception:
        pass
    
    # Style "New to trading?" label
    try:
        ui.lb_trading.setStyleSheet("QLabel { color: #757575; font-size: 12px; }")
    except Exception:
        pass

