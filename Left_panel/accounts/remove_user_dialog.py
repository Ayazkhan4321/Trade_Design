"""
Dialog for removing a user from profile
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, 
    QHBoxLayout, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from accounts.store import AppStore
from accounts.services.user_management import UserManagementService
from accounts.api.config import API_BASE_URL


class RemoveUserDialog(QDialog):
    """Dialog to confirm removal of a secondary user from profile"""
    
    user_removed = Signal(str)  # Signal emitted with the email of removed user
    
    def __init__(self, user_email, username, accounts, parent=None):
        """
        Initialize the remove user dialog
        
        Args:
            user_email: Email of the user to remove
            username: Username/fullname to display
            accounts: List of accounts that will be removed
            parent: Parent widget
        """
        super().__init__(parent)
        self.user_email = user_email
        self.username = username
        self.accounts = accounts
        
        self.setWindowTitle("Remove Profile")
        self.setMinimumWidth(550)
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
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton#removeButton {
                background-color: #dc2626;
                color: white;
            }
            QPushButton#removeButton:hover {
                background-color: #b91c1c;
            }
            QPushButton#removeButton:pressed {
                background-color: #991b1b;
            }
            QPushButton#cancelButton {
                background-color: #f1f5f9;
                color: #475569;
            }
            QPushButton#cancelButton:hover {
                background-color: #e2e8f0;
            }
            QScrollArea {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f8fafc;
            }
        """)
        
        # Title
        title_label = QLabel("Remove Profile")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #0f172a; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Confirmation message
        confirm_msg = QLabel(
            f"Are you sure you want to remove the profile for <b>{self.username}</b>?"
        )
        confirm_msg.setWordWrap(True)
        confirm_msg.setStyleSheet("color: #1e293b; font-size: 15px; margin-bottom: 10px;")
        layout.addWidget(confirm_msg)
        
        # Warning message
        warning_label = QLabel(f"This will remove access to all {len(self.accounts)} account(s):")
        warning_label.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 14px;")
        layout.addWidget(warning_label)
        
        # Scrollable accounts list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(5)
        
        # Add accounts to the list
        for acc in self.accounts:
            acc_number = acc.get('number', acc.get('accountNumber', 'Unknown'))
            acc_type = acc.get('accountTypeName', acc.get('accountName', ''))
            
            acc_label = QLabel(f"• {acc_number} - {acc_type}")
            acc_label.setStyleSheet("color: #475569; font-size: 13px; padding: 2px;")
            scroll_layout.addWidget(acc_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Cannot be undone warning
        undo_warning = QLabel("This action cannot be undone.")
        undo_warning.setStyleSheet("color: #dc2626; font-style: italic; font-size: 13px; margin-top: 10px;")
        layout.addWidget(undo_warning)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.remove_button = QPushButton("🗑 Remove Profile")
        self.remove_button.setObjectName("removeButton")
        self.remove_button.clicked.connect(self.on_remove_user)
        button_layout.addWidget(self.remove_button)
        
        layout.addLayout(button_layout)
    
    def on_remove_user(self):
        """Handle the remove user button click"""
        # Get primary user ID from store
        store = AppStore.instance()
        user_data = store.state.get("user", {})
        primary_user_id = user_data.get("userId")
        
        if not primary_user_id:
            QMessageBox.critical(
                self,
                "Error",
                "Could not find user ID. Please login again."
            )
            return
        
        # Get access token if available
        access_token = user_data.get("accessToken") or user_data.get("token")
        
        # Disable button during request
        self.remove_button.setEnabled(False)
        self.remove_button.setText("Removing...")
        
        # Call the service
        service = UserManagementService(API_BASE_URL, access_token)
        success, message, response_data = service.remove_user_from_profile(
            primary_user_id, self.user_email
        )
        
        # Re-enable button
        self.remove_button.setEnabled(True)
        self.remove_button.setText("🗑 Remove Profile")
        
        if success:
            # Emit signal with user email
            self.user_removed.emit(self.user_email)
            
            # Show success message
            QMessageBox.information(self, "Success", message)
            
            # Close dialog
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
