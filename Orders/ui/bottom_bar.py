from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer

from accounts.store import AppStore
from decimal import Decimal, InvalidOperation


class BottomBar(QWidget):
    def __init__(self, table_view, profit_col):
        super().__init__()

        self.table_view = table_view
        self.profit_col = profit_col

        self.setFixedHeight(40)
        self.setObjectName("orders_bottom_bar")

        # subtle top border and light background to separate from table
        self.setStyleSheet("background: #F9FAFB; border-top: 1px solid #E5E7EB;")

        # We'll put the left-side metrics into a content widget that we can
        # horizontally translate to match the table's horizontal scroll value.
        self.content = QWidget(self)
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(10, 4, 10, 4)
        content_layout.setSpacing(6)

        # left-side metrics
        self.balance = QLabel("Balance: 1,000,000")
        self.equity = QLabel("Equity: 1,000,000")
        self.margin = QLabel("Margin: 207.51")
        self.free_margin = QLabel("Free Margin: 999,999,792")
        self.margin_level = QLabel("Margin Level: 16,810,628.4")
        self.currency = QLabel("Currency: USD")

        # base typography for labels
        base_style = "font-size:12px; color:#1F2937;"
        for w in [self.balance, self.equity, self.margin, self.free_margin, self.margin_level, self.currency]:
            w.setStyleSheet(base_style)

        # separator maker
        def sep():
            s = QLabel("|")
            s.setStyleSheet("color: #CBD5E1; margin-left:6px; margin-right:6px;")
            s.setAlignment(Qt.AlignCenter)
            return s

        items = [self.balance, self.equity, self.margin, self.free_margin, self.margin_level, self.currency]
        for i, w in enumerate(items):
            content_layout.addWidget(w)
            if i != len(items) - 1:
                content_layout.addWidget(sep())

        content_layout.addStretch()

        # right-side Net P&L
        self.net_pl = QLabel("Net P&L: +0.51")

        # Create a floating container for Net P&L so we can move it relative to the table
        # NOTE: do NOT let the content layout manage this widget; we'll position it manually
        self.net_pl_container = QWidget(self)
        self.net_pl_container.setFixedHeight(32)
        net_layout = QHBoxLayout(self.net_pl_container)
        net_layout.setContentsMargins(0, 0, 0, 0)
        net_layout.addWidget(self.net_pl)
        self.net_pl_container.setVisible(True)
        self.net_pl_container.raise_()

        # Net P&L styling (dynamic color via method)
        self.net_pl.setStyleSheet("font-size:13px; font-weight:700; color:#22C55E;")

        # wire resizing and initial alignment (also listen to horizontal scroll)
        try:
            header = self.table_view.horizontalHeader()
            header.sectionResized.connect(self.align_net_pl)
            header.sectionMoved.connect(self.align_net_pl)
            # Move content in sync with table horizontal scrolling
            self.table_view.horizontalScrollBar().valueChanged.connect(self._on_table_hscroll)
            QTimer.singleShot(0, self._initial_layout)
        except Exception:
            pass

        # Subscribe to account changes so balance/currency update automatically
        try:
            store = AppStore.instance()
            store.account_changed.connect(self._on_account_changed)
            # Apply current store state immediately if available
            try:
                self._apply_api_state(store.get_current_account(), store.get_api_response())
            except Exception:
                pass
        except Exception:
            pass

    def align_net_pl(self):
        """Align Net P&L so it sits under the PROFIT/LOSS column.

        Use the header's viewport coordinates so alignment stays correct when
        the view is scrolled, resized, or columns are reordered.
        """
        try:
            header = self.table_view.horizontalHeader()

            # x position of PROFIT/LOSS column in header viewport coordinates
            x = header.sectionViewportPosition(self.profit_col)
            # account for content translation (we translate content by -scroll)
            scroll = 0
            try:
                scroll = self.table_view.horizontalScrollBar().value()
            except Exception:
                scroll = 0

            # if the column is not visible (x < 0) hide the net container
            if x < 0:
                self.net_pl_container.hide()
                return

            self.net_pl_container.show()
            # position inside this widget (small top padding)
            try:
                # When content is translated left by `scroll`, the local x inside
                # this widget must be x + scroll to align under the header column.
                self.net_pl_container.move(int(x + scroll), 4)
            except Exception:
                pass
        except Exception:
            pass

    def set_net_pl(self, value: float):
        """Update Net P&L text and color based on sign."""
        try:
            sign = "+" if value >= 0 else ""
            self.net_pl.setText(f"Net P&L: {sign}{value:.2f}")
            color = "#22C55E" if value >= 0 else "#EF4444"
            self.net_pl.setStyleSheet(f"font-size:13px; font-weight:700; color: {color};")
        except Exception:
            pass

    def set_currency(self, code: str):
        try:
            self.currency.setText(f"Currency: {code}")
        except Exception:
            pass

    def set_balance(self, amount):
        """Set formatted balance text. Accepts numeric or string-like values."""
        try:
            if amount is None:
                amt = 0.0
            else:
                # Use Decimal for robust formatting of very large numbers
                try:
                    d = Decimal(str(amount))
                    amt = float(d)
                except (InvalidOperation, ValueError):
                    amt = float(amount)

            # Format with thousands separator and two decimals
            self.balance.setText(f"Balance: {amt:,.2f}")
        except Exception:
            pass

    def _on_account_changed(self, account_info: dict):
        """Handler for AppStore.account_changed signal."""
        try:
            store = AppStore.instance()
            api_resp = store.get_api_response()
            self._apply_api_state(account_info, api_resp)
        except Exception:
            pass

    def _apply_api_state(self, current_account: dict, api_response: dict):
        """Extract account details (balance, currency) from the stored API response
        and update the bottom bar labels.

        This function handles both direct `accounts` and `sharedAccounts` payloads.
        """
        try:
            if not api_response:
                return

            # normalized account id fields (AppStore uses 'account_id')
            acct_id = None
            if current_account and isinstance(current_account, dict):
                acct_id = current_account.get('account_id') or current_account.get('accountId') or current_account.get('account_id')

            # Helper to try extract from a list of account dicts
            def find_in_list(lst):
                for a in lst or []:
                    try:
                        if acct_id is not None and int(a.get('accountId') or a.get('account_id') or 0) == int(acct_id):
                            return a
                    except Exception:
                        continue
                return None

            # 1) Direct accounts key
            candidate = None
            if isinstance(api_response, dict):
                candidate = find_in_list(api_response.get('accounts', []))

                # 2) sharedAccounts -> accounts
                if not candidate:
                    shared = api_response.get('sharedAccounts', [])
                    for group in shared or []:
                        candidate = find_in_list(group.get('accounts', []))
                        if candidate:
                            break

            # If we found an account, update labels
            if candidate:
                try:
                    bal = candidate.get('balance')
                    cur = candidate.get('currency') or candidate.get('accountCurrency')
                    self.set_balance(bal)
                    if cur:
                        self.set_currency(cur)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_table_hscroll(self, value: int):
        """Translate the left-side content to visually scroll with the table."""
        try:
            # move content left as table scrolls right
            self.content.move(-int(value), 0)
            # reposition net_pl relative to header+scroll
            self.align_net_pl()
        except Exception:
            pass

    def _initial_layout(self):
        # Ensure content fills horizontally so translation behaves predictably
        try:
            self.content.setFixedHeight(self.height())
            # place content at origin inside this widget
            self.content.move(0, 0)
            # initial alignment
            self.align_net_pl()
        except Exception:
            pass

    def set_margin_level(self, text: str):
        try:
            self.margin_level.setText(f"Margin Level: {text}")
        except Exception:
            pass
