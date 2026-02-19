"""Compatibility wrapper: prefer the canonical `accounts.store.AppStore`.

This module delegates to the central `accounts.store.AppStore` when available
so duplicate `Left_panel.accounts` copies do not create separate singletons.
If the canonical module cannot be imported (rare), fall back to a local
implementation for resilience.
"""

try:
    # Prefer the canonical store implementation
    from accounts.store import AppStore as AppStore
except Exception:
    # Fallback local implementation
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
                "api_response": None,
                "current_account": {
                    "account_number": None,
                    "owner_email": None,
                    "account_id": None,
                    "is_demo": False,
                    "is_own": True,
                }
            }

        @classmethod
        def instance(cls):
            if not cls._instance:
                cls._instance = cls()
            return cls._instance

        def set_user(self, user_data):
            self.state["user"] = user_data

        def set_accounts(self, live_own, demo_own, live_shared, demo_shared):
            self.state["accounts"]["live"]["own"] = live_own
            self.state["accounts"]["demo"]["own"] = demo_own
            self.state["accounts"]["live"]["shared"] = live_shared
            self.state["accounts"]["demo"]["shared"] = demo_shared

        def set_api_response(self, response):
            self.state["api_response"] = response

        def add_shared_accounts(self, shared_accounts_data):
            if not shared_accounts_data:
                return
            for shared_group in shared_accounts_data:
                owner = shared_group.get('accountOwner', {})
                accounts = shared_group.get('accounts', [])
                live_accounts = [acc for acc in accounts if not acc.get('isDemo', False)]
                demo_accounts = [acc for acc in accounts if acc.get('isDemo', False)]
                shared_entry = {
                    'username': owner.get('username', owner.get('fullName', 'Shared User')),
                    'email': (owner.get('email', '') or '').lower(),
                    'userId': owner.get('userId'),
                    'fullName': owner.get('fullName'),
                    'accounts': []
                }
                if live_accounts:
                    live_entry = shared_entry.copy()
                    live_entry['accounts'] = [{'number': acc.get('accountNumber') or acc.get('number'), **acc} for acc in live_accounts]
                    self.state["accounts"]["live"]["shared"].append(live_entry)
                if demo_accounts:
                    demo_entry = shared_entry.copy()
                    demo_entry['accounts'] = [{'number': acc.get('accountNumber') or acc.get('number'), **acc} for acc in demo_accounts]
                    self.state["accounts"]["demo"]["shared"].append(demo_entry)

        def remove_shared_accounts_by_email(self, email: str):
            target = (email or '').lower()
            self.state["accounts"]["live"]["shared"] = [
                group for group in self.state["accounts"]["live"]["shared"]
                if (group.get('email') or '').lower() != target
            ]
            self.state["accounts"]["demo"]["shared"] = [
                group for group in self.state["accounts"]["demo"]["shared"]
                if (group.get('email') or '').lower() != target
            ]

        def set_current_account(self, account_number, owner_email, is_own=True, account_id=None, is_demo=False):
            normalized_owner = (owner_email or '').lower()
            self.state["current_account"] = {
                "account_number": account_number,
                "owner_email": normalized_owner,
                "account_id": account_id,
                "is_demo": is_demo,
                "is_own": is_own,
                "can_trade": False,
            }
            try:
                self.account_changed.emit(self.state["current_account"])
                # Also emit account_id specifically for OrderUpdatesService
                if account_id:
                    self.account_id_changed.emit(int(account_id))
            except Exception:
                pass

        def get_current_account(self):
            return self.state["current_account"]

        def get_accounts(self):
            return self.state["accounts"]

        def get_api_response(self):
            return self.state["api_response"]
