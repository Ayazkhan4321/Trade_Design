from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QRadioButton, QButtonGroup


class SwitchAccountDialog(QDialog):
    """Dialog to verify credentials when switching to a different profile's account."""
    
    # email, password, is_trade_password
    account_verified = Signal(str, str, bool)
    
    def __init__(self, target_username, target_account, owner_email, parent=None):
        super().__init__(parent)
        self.target_username = target_username
        self.target_account = target_account
        self.owner_email = owner_email
        
        self.setWindowTitle("Verify Credentials")
        self.setModal(True)
        self.setFixedSize(700, 400)
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup the dialog UI matching the design in the image."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Verify Credentials")
        title_label.setObjectName("title_label")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_button = QPushButton("✕")
        close_button.setObjectName("close_button")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.reject)
        close_button.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Information text
        info_text = f"You are switching to <span style='color: #2563eb; font-weight: bold;'>{self.target_username}</span>'s account <span style='color: #f59e0b; font-weight: bold;'>{self.target_account}</span>.<br>"
        info_text += "<span style='color: #f59e0b; font-weight: 600;'>Please enter the credentials for this account's owner</span> to authorize the switch."
        
        info_label = QLabel(info_text)
        info_label.setObjectName("info_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Spacer
        layout.addSpacing(10)
        
        # Email field
        email_label = QLabel("Account Owner's Email")
        email_label.setObjectName("field_label")
        layout.addWidget(email_label)
        
        # Email input container
        email_container = QWidget()
        email_container.setObjectName("input_container")
        email_layout = QHBoxLayout(email_container)
        email_layout.setContentsMargins(15, 10, 15, 10)
        email_layout.setSpacing(10)
        
        email_icon = QLabel("✉")
        email_icon.setStyleSheet("font-size: 18px; color: #64748b;")
        email_layout.addWidget(email_icon)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("")
        self.email_input.setText(self.owner_email)
        self.email_input.setObjectName("email_input")
        self.email_input.setFrame(False)
        email_layout.addWidget(self.email_input)
        
        layout.addWidget(email_container)
        
        # Spacer
        layout.addSpacing(5)
        
        # Password field
        password_label = QLabel("Account Owner's Password")
        password_label.setObjectName("field_label")
        layout.addWidget(password_label)
        
        # Password input container
        password_container = QWidget()
        password_container.setObjectName("input_container")
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(15, 10, 15, 10)
        password_layout.setSpacing(10)
        
        password_icon = QLabel("🔑")
        password_icon.setStyleSheet("font-size: 18px; color: #64748b;")
        password_layout.addWidget(password_icon)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter account owner's password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("password_input")
        self.password_input.setFrame(False)
        password_layout.addWidget(self.password_input)
        
        # Show/hide password button
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setObjectName("show_password_btn")
        self.show_password_btn.setFixedSize(30, 30)
        self.show_password_btn.setCursor(Qt.PointingHandCursor)
        self.show_password_btn.clicked.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)
        
        layout.addWidget(password_container)

        # Password type selector (trade vs view)
        type_label = QLabel("Password Type")
        type_label.setObjectName("field_label")
        layout.addWidget(type_label)

        type_container = QWidget()
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)

        self.trade_radio = QRadioButton("Trade Password (full access)")
        self.view_radio = QRadioButton("View Password (read-only)")
        self.trade_radio.setChecked(True)

        self._pw_type_group = QButtonGroup(self)
        self._pw_type_group.addButton(self.trade_radio)
        self._pw_type_group.addButton(self.view_radio)

        type_layout.addWidget(self.trade_radio)
        type_layout.addWidget(self.view_radio)
        layout.addWidget(type_container)
        
        # Spacer
        layout.addStretch()
        
        # Button container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.setFixedSize(120, 45)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Switch Account button
        switch_button = QPushButton("Switch Account")
        switch_button.setObjectName("switch_button")
        switch_button.setFixedSize(160, 45)
        switch_button.setCursor(Qt.PointingHandCursor)
        switch_button.clicked.connect(self._handle_switch)
        button_layout.addWidget(switch_button)
        
        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        """Apply stylesheet to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
            
            #title_label {
                font-size: 24px;
                font-weight: 600;
                color: #1e293b;
            }
            
            #close_button {
                background-color: transparent;
                border: none;
                color: #64748b;
                font-size: 20px;
                border-radius: 15px;
            }
            
            #close_button:hover {
                background-color: #f1f5f9;
                color: #1e293b;
            }
            
            #info_label {
                font-size: 14px;
                color: #475569;
                line-height: 1.6;
            }
            
            #field_label {
                font-size: 13px;
                font-weight: 600;
                color: #475569;
            }
            
            #input_container {
                background-color: #ffffff;
                border: 2px solid #2563eb;
                border-radius: 8px;
            }
            
            #email_input, #password_input {
                font-size: 14px;
                color: #1e293b;
                background-color: transparent;
                border: none;
            }
            
            #email_input::placeholder, #password_input::placeholder {
                color: #94a3b8;
            }
            
            #show_password_btn {
                background-color: transparent;
                border: none;
                font-size: 16px;
            }
            
            #show_password_btn:hover {
                background-color: #f1f5f9;
                border-radius: 4px;
            }
            
            #cancel_button {
                background-color: #e2e8f0;
                color: #475569;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            
            #cancel_button:hover {
                background-color: #cbd5e1;
            }
            
            #cancel_button:pressed {
                background-color: #94a3b8;
            }
            
            #switch_button {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            
            #switch_button:hover {
                background-color: #1d4ed8;
            }
            
            #switch_button:pressed {
                background-color: #1e40af;
            }
        """)
    
    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def _handle_switch(self):
        """Handle the switch account button click."""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            # You could add a validation message here
            return
        
        # Determine password type
        is_trade = bool(self.trade_radio.isChecked())

        # Emit the credentials for verification
        self.account_verified.emit(email, password, is_trade)
        self.accept()

    def showEvent(self, event):
        """Ensure dialog is centered when shown (over parent if available)."""
        try:
            # Compute global center point: prefer parent's global center, else screen center
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QGuiApplication

            # Prefer centering over the top-level window (main window) if available
            parent = self.parent()
            parent_center_global = None
            if parent is not None:
                try:
                    top_window = parent.window()
                    # frameGeometry is in global coordinates
                    parent_center_global = top_window.frameGeometry().center()
                except Exception:
                    parent_center_global = None

            # Fallback to mapping parent's center to global if top-level failed
            if parent_center_global is None and parent is not None:
                try:
                    parent_center_global = parent.mapToGlobal(parent.rect().center())
                except Exception:
                    parent_center_global = None

            # Final fallback: primary screen center
            if parent_center_global is None:
                screen = QGuiApplication.primaryScreen()
                parent_center_global = screen.availableGeometry().center()

            # Calculate top-left so dialog is centered at parent_center_global
            w = self.width()
            h = self.height()
            top_left = QPoint(parent_center_global.x() - w // 2, parent_center_global.y() - h // 2)
            self.move(top_left)
        except Exception:
            pass

        return super().showEvent(event)
