from PySide6.QtWidgets import QTreeWidgetItem, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtCore import Qt
from accounts.store import AppStore

def build_accounts_tree(tree, add_user_callback=None, remove_user_callback=None):
    store = AppStore.instance()
    accounts = store.get_accounts()
    api_response = store.get_api_response()
    user_data = store.state.get("user", {})
    current_account = store.get_current_account()
    
    # Get username and email from stored user data or API response
    username = user_data.get("fullName") or user_data.get("email", "User")
    user_email = user_data.get("email", "")
    
    if not username or username == "User" or not user_email:
        if api_response:
            username = api_response.get("fullName") or api_response.get("username") or api_response.get("email", "User")
            if not user_email:
                user_email = api_response.get("email", "")
    
    # Extract username part before @ if it's an email
    if "@" in username:
        username = username.split("@")[0]

    tree.clear()

    # Root: TradePro Exchange with + button
    root = QTreeWidgetItem(tree)
    root.setExpanded(True)
    
    # Create a custom widget with label and + button
    root_widget = QWidget()
    root_layout = QHBoxLayout(root_widget)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(8)
    
    # Label for "TradePro Exchange"
    root_label = QLabel("TradePro Exchange")
    root_label.setStyleSheet("color: #1e293b; font-size: 14px;")
    root_layout.addWidget(root_label)
    
    # + button
    add_button = QPushButton("+")
    add_button.setFixedSize(20, 20)
    add_button.setStyleSheet("""
        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #1d4ed8;
        }
        QPushButton:pressed {
            background-color: #1e40af;
        }
    """)
    add_button.setCursor(Qt.PointingHandCursor)
    
    # Connect the button to the callback if provided
    if add_user_callback:
        add_button.clicked.connect(add_user_callback)
    
    root_layout.addWidget(add_button)
    root_layout.addStretch()
    
    # Set the widget for the root item
    tree.setItemWidget(root, 0, root_widget)

    # LIVE Accounts
    live = QTreeWidgetItem(root, ["TradePro Exchange - Live 🟢"])
    live.setExpanded(True)
    
    # User's own live accounts
    if accounts["live"]["own"]:
        user_node = QTreeWidgetItem(live, [username])
        user_node.setExpanded(True)
        
        print(f"\nDisplaying {len(accounts['live']['own'])} live accounts:")
        for idx, acc in enumerate(accounts["live"]["own"]):
            acc_number = str(acc["number"])
            print(f"  - {acc_number}")
            acc_item = QTreeWidgetItem(user_node, [acc_number])
            
            # Store account metadata for click handling
            acc_item.setData(0, Qt.UserRole + 1, acc_number)  # Account number
            acc_item.setData(0, Qt.UserRole + 2, None)  # None means own account
            acc_item.setData(0, Qt.UserRole + 3, user_email)  # Owner email
            
            # Highlight the active account in green
            if (current_account.get("account_number") == acc_number and 
                user_email and current_account.get("owner_email", "").lower() == user_email.lower()):
                acc_item.setForeground(0, QBrush(QColor(34, 197, 94)))  # Green color #22c55e
                font = acc_item.font(0)
                font.setBold(True)
                acc_item.setFont(0, font)

    # Shared live accounts
    for shared in accounts["live"]["shared"]:
        owner_name = shared.get("username", shared.get("owner", "Shared User"))
        owner_email = shared.get("email", "")
        owner_accounts = shared.get("accounts", [])
        
        # Skip if no email (shouldn't happen but safety check)
        if not owner_email:
            print(f"Warning: Shared user '{owner_name}' has no email, skipping delete button")
        
        owner = QTreeWidgetItem(live)
        owner.setExpanded(True)
        
        # Create widget with username and delete button
        owner_widget = QWidget()
        owner_widget.setAttribute(Qt.WA_TranslucentBackground)
        owner_layout = QHBoxLayout(owner_widget)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(8)
        
        owner_label = QLabel(owner_name)
        owner_label.setStyleSheet("color: #64748b; font-size: 14px;")
        owner_layout.addWidget(owner_label)
        
        # Delete button (trash icon)
        delete_button = QPushButton("🗑")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc2626;
                border: none;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
        """)
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setVisible(True)  # Always visible for testing
        delete_button.setFocusPolicy(Qt.NoFocus)
        
        # Connect delete button if callback provided and email exists
        if remove_user_callback and owner_email:
            def on_delete_clicked():
                print(f"\n*** DELETE BUTTON CLICKED ***")
                print(f"User: {owner_name}")
                print(f"Email: {owner_email}")
                print(f"Accounts: {len(owner_accounts)}")
                remove_user_callback(owner_email, owner_name, owner_accounts)
            
            delete_button.clicked.connect(on_delete_clicked)
            print(f"Connected delete button for {owner_name} ({owner_email})")
        elif not owner_email:
            # Disable button if no email
            delete_button.setEnabled(False)
            print(f"No email for {owner_name}, button disabled")
        
        owner_layout.addWidget(delete_button)
        owner_layout.addStretch()
        
        tree.setItemWidget(owner, 0, owner_widget)
        
        # Store button reference for hover handling
        owner.setData(0, Qt.UserRole, delete_button)
        
        print(f"\nShared live accounts from {owner_name}:")
        for acc in owner_accounts:
            acc_number = str(acc["number"])
            print(f"  - {acc_number}")
            acc_item = QTreeWidgetItem(owner, [acc_number])
            
            # Store account metadata for click handling
            acc_item.setData(0, Qt.UserRole + 1, acc_number)  # Account number
            acc_item.setData(0, Qt.UserRole + 2, owner_name)  # Owner name for shared account
            acc_item.setData(0, Qt.UserRole + 3, owner_email)  # Owner email
            
            # Highlight the active account in green if it's from this shared user
            if (current_account.get("account_number") == acc_number and 
                current_account.get("owner_email", "").lower() == owner_email.lower()):
                acc_item.setForeground(0, QBrush(QColor(34, 197, 94)))  # Green color #22c55e
                font = acc_item.font(0)
                font.setBold(True)
                acc_item.setFont(0, font)

    # DEMO Accounts
    demo = QTreeWidgetItem(root, ["TradePro Exchange - Demo"])
    demo.setExpanded(True)
    
    # User's own demo accounts
    if accounts["demo"]["own"]:
        user_demo = QTreeWidgetItem(demo, [username])
        user_demo.setExpanded(True)
        
        print(f"\nDisplaying {len(accounts['demo']['own'])} demo accounts:")
        for acc in accounts["demo"]["own"]:
            acc_number = str(acc["number"])
            print(f"  - {acc_number}")
            acc_item = QTreeWidgetItem(user_demo, [acc_number])
            
            # Store account metadata for click handling
            acc_item.setData(0, Qt.UserRole + 1, acc_number)  # Account number
            acc_item.setData(0, Qt.UserRole + 2, None)  # None means own account
            acc_item.setData(0, Qt.UserRole + 3, user_email)  # Owner email
            
            # Highlight the active account in green
            if (current_account.get("account_number") == acc_number and 
                user_email and current_account.get("owner_email", "").lower() == user_email.lower()):
                acc_item.setForeground(0, QBrush(QColor(34, 197, 94)))  # Green color #22c55e
                font = acc_item.font(0)
                font.setBold(True)
                acc_item.setFont(0, font)
    
    # Shared demo accounts
    for shared in accounts["demo"]["shared"]:
        owner_name = shared.get("username", shared.get("owner", "Shared User"))
        owner_email = shared.get("email", "")
        owner_accounts = shared.get("accounts", [])
        
        # Skip if no email (shouldn't happen but safety check)
        if not owner_email:
            print(f"Warning: Shared user '{owner_name}' has no email, skipping delete button")
        
        owner = QTreeWidgetItem(demo)
        owner.setExpanded(True)
        
        # Create widget with username and delete button
        owner_widget = QWidget()
        owner_widget.setAttribute(Qt.WA_TranslucentBackground)
        owner_layout = QHBoxLayout(owner_widget)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(8)
        
        owner_label = QLabel(owner_name)
        owner_label.setStyleSheet("color: #64748b; font-size: 14px;")
        owner_layout.addWidget(owner_label)
        
        # Delete button (trash icon)
        delete_button = QPushButton("🗑")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc2626;
                border: none;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
        """)
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setVisible(True)  # Always visible for testing
        delete_button.setFocusPolicy(Qt.NoFocus)
        
        # Connect delete button if callback provided and email exists
        if remove_user_callback and owner_email:
            def on_delete_clicked():
                print(f"\n*** DELETE BUTTON CLICKED (DEMO) ***")
                print(f"User: {owner_name}")
                print(f"Email: {owner_email}")
                print(f"Accounts: {len(owner_accounts)}")
                remove_user_callback(owner_email, owner_name, owner_accounts)
            
            delete_button.clicked.connect(on_delete_clicked)
            print(f"Connected delete button for {owner_name} ({owner_email})")
        elif not owner_email:
            # Disable button if no email
            delete_button.setEnabled(False)
            print(f"No email for {owner_name}, button disabled")
        
        owner_layout.addWidget(delete_button)
        owner_layout.addStretch()
        
        tree.setItemWidget(owner, 0, owner_widget)
        
        # Store button reference for hover handling
        owner.setData(0, Qt.UserRole, delete_button)
        
        print(f"\nShared demo accounts from {owner_name}:")
        for acc in owner_accounts:
            acc_number = str(acc["number"])
            print(f"  - {acc_number}")
            acc_item = QTreeWidgetItem(owner, [acc_number])
            
            # Store account metadata for click handling
            acc_item.setData(0, Qt.UserRole + 1, acc_number)  # Account number
            acc_item.setData(0, Qt.UserRole + 2, owner_name)  # Owner name for shared account
            acc_item.setData(0, Qt.UserRole + 3, owner_email)  # Owner email
            
            # Highlight the active account in green if it's from this shared user
            if (current_account.get("account_number") == acc_number and 
                current_account.get("owner_email", "").lower() == owner_email.lower()):
                acc_item.setForeground(0, QBrush(QColor(34, 197, 94)))  # Green color #22c55e
                font = acc_item.font(0)
                font.setBold(True)
                acc_item.setFont(0, font)

    tree.expandAll()
    print("\nTree built successfully!\n")
