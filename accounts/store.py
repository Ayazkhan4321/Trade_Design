from PySide6.QtCore import QObject, Signal


class AppStore(QObject):
    account_changed = Signal(dict)  # Emitted when current account changes
    account_id_changed = Signal(int)  # Emitted when account_id is set/changed (for simple subscribers)

    _instance = None

    def __init__(self):
        super().__init__()
        self.state = {
            "user": {},
            "accounts": {
                "live": {"own": [], "shared": []},
                "demo": {"own": [], "shared": []}
            },
            "api_response": None,  # Store full API response
            "current_account": {
                "account_number": None,
                "owner_email": None,  # Email of the account owner (current user or shared user)
                "account_id": None,
                "is_demo": False,
                "is_own": True  # True if it's the user's own account, False if shared
            }
        }

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    # --------- ACTIONS ----------
    def set_user(self, user_data):
        self.state["user"] = user_data

    def set_accounts(self, live_own, demo_own, live_shared, demo_shared):
        self.state["accounts"]["live"]["own"] = live_own
        self.state["accounts"]["demo"]["own"] = demo_own
        self.state["accounts"]["live"]["shared"] = live_shared
        self.state["accounts"]["demo"]["shared"] = demo_shared
    
    def set_api_response(self, response):
        """Store the full API response for reference."""
        self.state["api_response"] = response
    
    def add_shared_accounts(self, shared_accounts_data):
        """Add shared accounts from API response to the store.
        
        Args:
            shared_accounts_data: List of shared account groups from API response
                Format: [{'accountOwner': {...}, 'accounts': [...]}]
        """
        if not shared_accounts_data:
            return
        
        for shared_group in shared_accounts_data:
            owner = shared_group.get('accountOwner', {})
            accounts = shared_group.get('accounts', [])
            
            # Separate live and demo accounts
            live_accounts = [acc for acc in accounts if not acc.get('isDemo', False)]
            demo_accounts = [acc for acc in accounts if acc.get('isDemo', False)]
            
            # Format for the tree structure
            # Normalize owner email to lowercase for consistent comparisons
            shared_entry = {
                'username': owner.get('username', owner.get('fullName', 'Shared User')),
                'email': (owner.get('email', '') or '').lower(),  # store lowercase email
                'userId': owner.get('userId'),
                'fullName': owner.get('fullName'),
                'accounts': []
            }
            
            # Add live shared accounts if any
            if live_accounts:
                live_entry = shared_entry.copy()
                live_entry['accounts'] = [{'number': acc.get('accountNumber') or acc.get('number'), **acc} for acc in live_accounts]
                # email already normalized in shared_entry
                self.state["accounts"]["live"]["shared"].append(live_entry)
            
            # Add demo shared accounts if any
            if demo_accounts:
                demo_entry = shared_entry.copy()
                demo_entry['accounts'] = [{'number': acc.get('accountNumber') or acc.get('number'), **acc} for acc in demo_accounts]
                # email already normalized in shared_entry
                self.state["accounts"]["demo"]["shared"].append(demo_entry)
    
    def remove_shared_accounts_by_email(self, email: str):
        """Remove shared accounts for a specific user by email.
        
        Args:
            email: Email of the user whose shared accounts should be removed
        """
        # Normalize input email for case-insensitive match
        target = (email or '').lower()

        # Remove from live shared accounts
        self.state["accounts"]["live"]["shared"] = [
            group for group in self.state["accounts"]["live"]["shared"]
            if (group.get('email') or '').lower() != target
        ]
        
        # Remove from demo shared accounts
        self.state["accounts"]["demo"]["shared"] = [
            group for group in self.state["accounts"]["demo"]["shared"]
            if (group.get('email') or '').lower() != target
        ]

    def set_current_account(self, account_number, owner_email, is_own=True, account_id=None, is_demo=False):
        """Set the currently active account.
        
        Args:
            account_number: The account number
            owner_email: Email of the account owner
            is_own: True if it's the user's own account, False if shared
        """
        # normalize owner email to lowercase for consistent comparisons across app
        normalized_owner = (owner_email or '').lower()
        self.state["current_account"] = {
            "account_number": account_number,
            "owner_email": normalized_owner,
            "account_id": account_id,
            "is_demo": is_demo,
            "is_own": is_own,
            # default permission flag; callers may override
            "can_trade": False,
        }

        # Emit signals so subscribers (MarketWidget, OrdersWidget, etc.) can react
        try:
            print(f"[AppStore] Emitting account_changed: {self.state['current_account']}")
            self.account_changed.emit(self.state["current_account"])
            
            # Also emit account_id specifically for OrderUpdatesService
            if account_id:
                self.account_id_changed.emit(int(account_id))
        except Exception:
            import traceback
            traceback.print_exc()
    
    def get_current_account(self):
        """Get the currently active account information."""
        return self.state["current_account"]

    # --------- SELECTORS ----------
    def get_accounts(self):
        return self.state["accounts"]
    
    def get_api_response(self):
        """Get the full stored API response."""
        return self.state["api_response"]
