"""
Dialog for adding a user to the profile
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from accounts.store import AppStore
from accounts.services.user_management import UserManagementService
from accounts.api.config import API_BASE_URL


class AddUserDialog(QDialog):
    """Dialog to add a secondary user to the profile"""
    
    user_added = Signal(dict, str)  # Signal emitted with (response_data, message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User to Profile")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Apply stylesheet
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1e293b;
                font-size: 14px;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 14px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
                padding: 9px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton#primaryButton {
                background-color: #2563eb;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1e40af;
            }
            QPushButton#secondaryButton {
                background-color: #f1f5f9;
                color: #475569;
            }
            QPushButton#secondaryButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        # Title
        title_label = QLabel("Add User to Profile")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #0f172a; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Add a secondary user to your profile by entering their email/account number and password."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Email or Account Number field
        email_label = QLabel("Secondary User Email or Account Number:")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email or account number")
        layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Secondary User Password:")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.add_button = QPushButton("Add User")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.on_add_user)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
    
    def on_add_user(self):
        """Handle the add user button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not email:
            QMessageBox.warning(self, "Validation Error", "Please enter an email or account number.")
            self.email_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Validation Error", "Please enter a password.")
            self.password_input.setFocus()
            return
        
        # Basic validation - accept either email format or numeric account number
        is_email = "@" in email and "." in email
        is_account_number = email.isdigit()
        
        if not is_email and not is_account_number:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Please enter a valid email address or account number."
            )
            self.email_input.setFocus()
            return
        
        # Get primary user ID from store
        store = AppStore.instance()
        user_data = store.state.get("user", {})
        
        # Try multiple possible field names for user ID
        primary_user_id = (
            user_data.get("userId") or 
            user_data.get("id") or 
            user_data.get("roleId")
        )
        
        if not primary_user_id:
            # Debug: Print what's in the store
            print("\n" + "="*60)
            print("DEBUG: User data in store:")
            print(user_data)
            print("="*60 + "\n")
            
            QMessageBox.critical(
                self, 
                "Error", 
                "Could not find user ID. Please login again.\n\nAvailable fields: " + str(list(user_data.keys()))
            )
            return
        
        # Get access token if available
        access_token = user_data.get("accessToken") or user_data.get("token")
        
        # Disable button during request
        self.add_button.setEnabled(False)
        self.add_button.setText("Adding...")
        
        # Call the service
        service = UserManagementService(API_BASE_URL, access_token)
        success, message, response_data = service.add_user_to_profile(
            primary_user_id, email, password
        )
        
        # Re-enable button
        self.add_button.setEnabled(True)
        self.add_button.setText("Add User")
        
        if success:
            # Emit signal with response data and message
            self.user_added.emit(response_data or {}, message)
            
            # Close dialog
            self.accept()
        else:
            # Provide more context for specific error cases
            if "no owned accounts" in message.lower():
                error_msg = (
                    f"{message}\n\n"
                    "The user you're trying to add doesn't have any accounts yet. "
                    "They need to create at least one account before they can be added to your profile."
                )
            else:
                error_msg = message
            
            QMessageBox.critical(self, "Error", error_msg)
