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

        # 1. State variables
        self._val_balance = "1,000,000"
        self._val_equity = "1,000,000"
        self._val_margin = "207.51"
        self._val_free_margin = "999,999,792"
        self._val_margin_level = "16,810,628.4"
        self._val_currency = "USD"
        self._val_net_pl = 0.51
        self._separators = []

        # 2. Container Styling
        try:
            from Theme.theme_manager import ThemeManager
            mgr = ThemeManager.instance()
            t = mgr.tokens()
            self.setStyleSheet(
                f"#orders_bottom_bar {{ background: {t['bg_bottom_bar']}; border-top: 1px solid {t['border_separator']}; }}"
            )
            def _on_theme_changed_bottom_bar(name, tok, w=self):
                try:
                    w.setStyleSheet(
                        f"#orders_bottom_bar {{ background: {tok['bg_bottom_bar']}; border-top: 1px solid {tok['border_separator']}; }}"
                    )
                    w._refresh_all_labels()
                except RuntimeError:
                    pass
            mgr.theme_changed.connect(_on_theme_changed_bottom_bar)
        except Exception:
            self.setStyleSheet("#orders_bottom_bar { background: #F9FAFB; border-top: 1px solid #E5E7EB; }")

        self.content = QWidget(self)
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(10, 4, 10, 4)
        content_layout.setSpacing(6)

        # 3. Create the Labels
        self.currency = QLabel()
        self.balance = QLabel()
        self.equity = QLabel()
        self.margin = QLabel()
        self.free_margin = QLabel()
        self.margin_level = QLabel()

        def sep():
            s = QLabel("|")
            s.setAlignment(Qt.AlignCenter)
            self._separators.append(s)
            return s

        items = [self.currency, self.balance, self.equity, self.margin, self.free_margin, self.margin_level]
        for i, w in enumerate(items):
            content_layout.addWidget(w)
            if i != len(items) - 1:
                content_layout.addWidget(sep())

        content_layout.addStretch()

        # 4. Right-side Net P&L (Floating container anchored to the far right)
        self.net_pl = QLabel()
        self.net_pl_container = QWidget(self)
        self.net_pl_container.setFixedHeight(32)
        net_layout = QHBoxLayout(self.net_pl_container)
        net_layout.setContentsMargins(0, 0, 10, 0)
        net_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        net_layout.addWidget(self.net_pl)
        self.net_pl_container.show()
        self.net_pl_container.raise_()

        # 5. Apply Initial Formatting
        self._refresh_all_labels()

        try:
            self.table_view.horizontalScrollBar().valueChanged.connect(self._on_table_hscroll)
            QTimer.singleShot(0, self._initial_layout)
        except Exception:
            pass

        try:
            store = AppStore.instance()
            store.account_changed.connect(self._on_account_changed)
            try:
                self._apply_api_state(store.get_current_account(), store.get_api_response())
            except Exception:
                pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # UI Formatting Helpers
    # -------------------------------------------------------------------------
    def _format_label(self, title: str, value: str, value_color: str = None) -> str:
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            # 🟢 FIX: Grab the actual 'accent' theme color for the names so they pop!
            color_title = tok.get("accent", "#1976d2") 
            if not value_color:
                value_color = tok.get("text_primary", "#1F2937")
        except Exception:
            color_title = "#1976d2"
            if not value_color:
                value_color = "#1F2937"
            
        # Added font-weight:600 to the title so the theme color stands out nicely
        return f"<span style='color:{color_title}; font-size:12px; font-weight:600;'>{title}:</span> &nbsp;<b style='color:{value_color}; font-size:12px;'>{value}</b>"

    def _refresh_all_labels(self):
        try:
            self.currency.setText(self._format_label("Currency", self._val_currency))
            self.balance.setText(self._format_label("Balance", self._val_balance))
            self.equity.setText(self._format_label("Equity", self._val_equity))
            self.margin.setText(self._format_label("Margin", self._val_margin))
            self.free_margin.setText(self._format_label("Free Margin", self._val_free_margin))
            self.margin_level.setText(self._format_label("Margin Level", self._val_margin_level, value_color="#22C55E"))
            self.set_net_pl(self._val_net_pl) 
            
            try:
                from Theme.theme_manager import ThemeManager
                tok = ThemeManager.instance().tokens()
                sep_c = tok.get("border_separator", "#CBD5E1")
            except Exception:
                sep_c = "#CBD5E1"
            for s in self._separators:
                s.setStyleSheet(f"color: {sep_c}; margin-left:6px; margin-right:6px;")
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Layout and Updating Methods
    # -------------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            w = 200
            self.net_pl_container.setGeometry(self.width() - w, 4, w, 32)
            self.content.resize(max(self.width(), self.content.sizeHint().width()), self.height())
        except Exception:
            pass

    def align_net_pl(self):
        pass

    def set_net_pl(self, value: float):
        try:
            self._val_net_pl = value
            sign = "+" if value >= 0 else ""
            color = "#22C55E" if value >= 0 else "#EF4444"
            try:
                from Theme.theme_manager import ThemeManager
                tok = ThemeManager.instance().tokens()
                # 🟢 FIX: Ensure Net P&L title also gets the accent color
                title_color = tok.get("accent", "#1976d2") 
            except Exception:
                title_color = "#1976d2"
                
            self.net_pl.setText(
                f"<span style='color:{title_color}; font-size:13px; font-weight:600;'>Net P&L:</span> "
                f"&nbsp;<b style='color:{color}; font-size:13px;'>{sign}{value:.2f}</b>"
            )
        except Exception:
            pass

    def set_currency(self, code: str):
        try:
            self._val_currency = code
            self.currency.setText(self._format_label("Currency", self._val_currency))
        except Exception:
            pass

    def set_balance(self, amount):
        try:
            if amount is None:
                amt = 0.0
            else:
                try:
                    d = Decimal(str(amount))
                    amt = float(d)
                except (InvalidOperation, ValueError):
                    amt = float(amount)

            self._val_balance = f"{amt:,.2f}"
            self.balance.setText(self._format_label("Balance", self._val_balance))
        except Exception:
            pass

    def set_margin_level(self, text: str):
        try:
            self._val_margin_level = text
            self.margin_level.setText(self._format_label("Margin Level", self._val_margin_level, value_color="#22C55E"))
        except Exception:
            pass

    def _on_account_changed(self, account_info: dict):
        try:
            store = AppStore.instance()
            api_resp = store.get_api_response()
            self._apply_api_state(account_info, api_resp)
        except Exception:
            pass

    def _apply_api_state(self, current_account: dict, api_response: dict):
        try:
            if not api_response:
                return

            acct_id = None
            if current_account and isinstance(current_account, dict):
                acct_id = current_account.get('account_id') or current_account.get('accountId') or current_account.get('account_id')

            def find_in_list(lst):
                for a in lst or []:
                    try:
                        if acct_id is not None and int(a.get('accountId') or a.get('account_id') or 0) == int(acct_id):
                            return a
                    except Exception:
                        continue
                return None

            candidate = None
            if isinstance(api_response, dict):
                candidate = find_in_list(api_response.get('accounts', []))
                if not candidate:
                    shared = api_response.get('sharedAccounts', [])
                    for group in shared or []:
                        candidate = find_in_list(group.get('accounts', []))
                        if candidate:
                            break

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
        try:
            self.content.move(-int(value), 0)
        except Exception:
            pass

    def _initial_layout(self):
        try:
            self.content.setFixedHeight(self.height())
            self.content.move(0, 0)
        except Exception:
            pass