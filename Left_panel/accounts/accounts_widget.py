import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QMessageBox
from PySide6.QtCore import Qt, QEvent, QThread, Signal

from Login.login_page import LoginPage
from accounts.store import AppStore
from accounts.accounts_tree import build_accounts_tree
from accounts.add_user_dialog import AddUserDialog
from accounts.remove_user_dialog import RemoveUserDialog
from accounts.switch_account_dialog import SwitchAccountDialog
from accounts.login_worker import LoginWorker


class AccountsWidget(QWidget):
    """Pure QWidget implementation of the Accounts UI.

    Emits `statusMessage` when it wants to show a status update;
    if embedded inside a QMainWindow the host can forward these to its statusBar.
    """

    statusMessage = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Keep a reference to the store and any background threads
        self.store = AppStore.instance()

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tree widget for accounts
        self.accounts_tree = QTreeWidget()
        self.accounts_tree.setHeaderHidden(True)
        self.accounts_tree.setStyleSheet("")
        layout.addWidget(self.accounts_tree)

        # Connect events
        self.accounts_tree.setMouseTracking(True)
        self.accounts_tree.viewport().installEventFilter(self)
        self.accounts_tree.itemClicked.connect(self.on_account_clicked)

    # --- Status helper ---
    def show_status(self, message, timeout=0):
        # Emit signal and also try to forward to parent statusBar if available
        try:
            self.statusMessage.emit(message, timeout)
        except Exception:
            pass
        try:
            if hasattr(self.parent(), 'statusBar'):
                sb = self.parent().statusBar()
                if sb:
                    sb.showMessage(message, timeout)
        except Exception:
            pass

    # --- Login flow ---
    def show_login(self):
        # Reuse the single app-wide LoginPage so styles and behaviour are
        # consistent regardless of where login is invoked from.
        login_dialog = LoginPage(self)

        try:
            from Forgot_password.forgot_password_controller import ForgotPasswordDialog
            login_dialog.forgot_password_requested.connect(lambda: ForgotPasswordDialog(self).exec())
        except Exception:
            pass

        # Show dialog modally. After exec, consume `response_data` placed on the dialog
        # by the worker so we have the full API payload available.
        result = login_dialog.exec()
        try:
            if hasattr(login_dialog, 'response_data') and login_dialog.response_data:
                self.on_login_success(login_dialog.response_data)
        except Exception:
            pass

        return result

    def on_login_success(self, login_response):
        # Accept either: (a) full response dict/object emitted by older LoginPage,
        # or (b) a simple email `str` emitted by the centralized LoginPage.
        email = None
        data = None
        if isinstance(login_response, dict) or isinstance(login_response, list):
            data = login_response.get("data", login_response) if isinstance(login_response, dict) else None
            if data:
                email = data.get("email")
                # Populate the central store with the API response so downstream
                # components (MarketWidget, accounts tree) have the data they need.
                try:
                    from accounts.account_mapper import map_login_response
                    # Store full API response
                    self.store.set_api_response(data)
                    # Persist user
                    email_to_store = data.get("email") or email
                    self.store.set_user({
                        "userId": data.get("userId"),
                        "role": data.get("role"),
                        "roleId": data.get("roleId"),
                        "fullName": data.get("fullName"),
                        "email": email_to_store,
                        "accessToken": data.get("accessToken"),
                        "token": data.get("token"),
                    })
                    # Map and set accounts into store
                    live_own, demo_own, live_shared, demo_shared = map_login_response(data)
                    self.store.set_accounts(live_own, demo_own, live_shared, demo_shared)
                except Exception:
                    pass
        elif isinstance(login_response, str):
            # Email-only signal
            email = login_response

        # Store the API response data on this widget instance for callers
        self.api_response = {
            "user": self.store.state.get("user"),
            "accounts": self.store.state.get("accounts"),
        }

        # Set a default current account (if present)
        try:
            if self.store.state["accounts"]["live"]["own"]:
                first_account = self.store.state["accounts"]["live"]["own"][0]
                acct_number = first_account.get("number") or first_account.get("accountNumber") or str(first_account.get("id") or "")
                # Prefer numeric account id (accountId or id) when available so MarketDataService
                # can subscribe using the backend account identifier instead of the visible
                # account number string.
                acct_id = first_account.get("accountId") or first_account.get("id") or None
                self.store.set_current_account(
                    str(acct_number),
                    email or self.store.state.get("user", {}).get("email", ""),
                    is_own=True,
                    account_id=acct_id,
                )
        except Exception:
            pass

        # Build the accounts tree
        build_accounts_tree(self.accounts_tree, self.on_add_user_clicked, self.on_remove_user_clicked)

        # Update status
        self.show_status(f"Logged in as: {email}")

    # --- Event handling & tree helpers ---
    def eventFilter(self, obj, event):
        if obj == self.accounts_tree.viewport():
            if event.type() == QEvent.MouseMove:
                item = self.accounts_tree.itemAt(event.position().toPoint())
                self._update_delete_button_visibility(item)
            elif event.type() == QEvent.Leave:
                self._update_delete_button_visibility(None)
        return super().eventFilter(obj, event)

    def _update_delete_button_visibility(self, hovered_item):
        from PySide6.QtWidgets import QTreeWidgetItemIterator
        iterator = QTreeWidgetItemIterator(self.accounts_tree)
        while iterator.value():
            item = iterator.value()
            delete_button = item.data(0, Qt.UserRole)
            if delete_button:
                delete_button.setVisible(item == hovered_item)
            iterator += 1

    # --- Dialog actions ---
    def on_add_user_clicked(self):
        dialog = AddUserDialog(self)
        dialog.user_added.connect(self.on_user_added)
        dialog.exec()

    def on_remove_user_clicked(self, user_email, username, accounts):
        dialog = RemoveUserDialog(user_email, username, accounts, self)
        dialog.user_removed.connect(self.on_user_removed)
        dialog.exec()

    def on_user_added(self, response_data, api_message):
        shared_accounts = response_data.get('sharedAccounts', [])
        if shared_accounts:
            self.store.add_shared_accounts(shared_accounts)
            build_accounts_tree(self.accounts_tree, self.on_add_user_clicked, self.on_remove_user_clicked)
        QMessageBox.information(self, "Success", api_message)

    def on_user_removed(self, user_email):
        self.store.remove_shared_accounts_by_email(user_email)
        build_accounts_tree(self.accounts_tree, self.on_add_user_clicked, self.on_remove_user_clicked)

    # --- Account switching ---
    def on_account_clicked(self, item, column):
        account_text = item.text(column)
        if not (account_text.isdigit() or account_text.startswith('D')):
            return
        account_number = account_text

        accounts = self.store.get_accounts()
        user_data = self.store.state.get("user", {})
        current_user_email = user_data.get("email", "").lower()

        owner_email = None
        owner_username = None
        is_own = False

        for acc in accounts["live"]["own"]:
            if str(acc["number"]) == account_number:
                owner_email = current_user_email
                owner_username = user_data.get("fullName") or user_data.get("email", "User")
                is_own = True
                break

        if not owner_email:
            for acc in accounts["demo"]["own"]:
                if str(acc["number"]) == account_number:
                    owner_email = current_user_email
                    owner_username = user_data.get("fullName") or user_data.get("email", "User")
                    is_own = True
                    break

        if not owner_email:
            for shared_group in accounts["live"]["shared"]:
                for acc in shared_group.get("accounts", []):
                    if str(acc["number"]) == account_number:
                        owner_email = shared_group.get("email", "").lower()
                        owner_username = shared_group.get("username", "Shared User")
                        is_own = False
                        break
                if owner_email:
                    break

        if not owner_email:
            for shared_group in accounts["demo"]["shared"]:
                for acc in shared_group.get("accounts", []):
                    if str(acc["number"]) == account_number:
                        owner_email = shared_group.get("email", "").lower()
                        owner_username = shared_group.get("username", "Shared User")
                        is_own = False
                        break
                if owner_email:
                    break

        if not owner_email:
            return

        current_account = self.store.get_current_account()
        if (current_account.get("account_number") == account_number and 
            current_account.get("owner_email", "").lower() == owner_email):
            return

        current_active_owner = current_account.get("owner_email", "").lower()

        if owner_email == current_user_email or owner_email == current_active_owner:
            self.switch_account(account_number, owner_email, is_own)
        else:
            self.show_verify_credentials_dialog(account_number, owner_email, owner_username)

    def show_verify_credentials_dialog(self, account_number, owner_email, owner_username):
        dialog = SwitchAccountDialog(owner_username, account_number, owner_email, self)
        dialog.account_verified.connect(
            lambda email, password, is_trade: self.verify_and_switch_account(account_number, email, password, owner_email, is_trade)
        )
        dialog.exec()

    def verify_and_switch_account(self, account_number, email, password, expected_owner_email, is_trade_password=False):
        self.switch_thread = QThread(self)
        self.switch_worker = LoginWorker()
        self.switch_worker.moveToThread(self.switch_thread)

        self._pending_switch_account = account_number
        self._pending_switch_email = email
        self._pending_switch_expected_email = expected_owner_email
        self._pending_switch_is_trade = is_trade_password

        self.switch_thread.started.connect(lambda: self.switch_worker.run("live", email, password))
        self.switch_worker.finished.connect(self._on_switch_worker_finished)
        self.switch_worker.finished.connect(self.switch_thread.quit)
        self.switch_worker.finished.connect(self.switch_worker.deleteLater)
        self.switch_thread.finished.connect(self.switch_thread.deleteLater)
        self.switch_thread.start()

    def _on_switch_worker_finished(self, success, message, response_data):
        self.on_verify_complete(
            success,
            message,
            response_data,
            self._pending_switch_account,
            self._pending_switch_email,
            self._pending_switch_expected_email,
            getattr(self, '_pending_switch_is_trade', False)
        )

    def on_verify_complete(self, success, message, response_data, account_number, email, expected_owner_email, is_trade_password=False):
        if not success:
            QMessageBox.warning(self, "Verification Failed", f"Could not verify credentials: {message}")
            return

        if email.lower() != expected_owner_email.lower():
            QMessageBox.warning(self, "Verification Failed", "The provided credentials do not match the account owner.")
            return

        # Try to extract numeric account id from the verification response if present.
        acct_id = None
        try:
            # response_data may contain the full API payload under 'data'
            data = response_data.get("data", response_data) if isinstance(response_data, dict) else None
            accounts = data.get("accounts", []) if isinstance(data, dict) else []
            # Find matching account by accountNumber/number and prefer its accountId
            for acc in accounts:
                if str(acc.get("accountNumber") or acc.get("number") or "") == str(account_number):
                    acct_id = acc.get("accountId") or acc.get("id")
                    break
        except Exception:
            acct_id = None

        self.store.set_current_account(account_number, email.lower(), is_own=False, account_id=acct_id, is_demo=False)
        self.store.state['current_account']['can_trade'] = bool(is_trade_password)

        build_accounts_tree(self.accounts_tree, self.on_add_user_clicked, self.on_remove_user_clicked)

        original_user = self.store.state.get("user", {})
        original_email = original_user.get("email", "")
        self.show_status(f"Logged in as: {original_email} | Active account: {account_number} ({email})")

    def switch_account(self, account_number, owner_email, is_own):
        self.store.set_current_account(account_number, owner_email.lower(), is_own)
        build_accounts_tree(self.accounts_tree, self.on_add_user_clicked, self.on_remove_user_clicked)
        current_user = self.store.state.get("user", {})
        current_email = current_user.get("email", "")
        self.show_status(f"Logged in as: {current_email} | Active account: {account_number}", 5000)
