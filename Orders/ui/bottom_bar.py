from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from accounts.store import AppStore


class BottomBar(QWidget):
    def __init__(self, table_view, profit_col_index):
        super().__init__()
        self.table_view = table_view
        self.profit_col_index = profit_col_index
        self.setFixedHeight(32)
        self.setObjectName("orders_bottom_bar")

        # ── Raw state (always floats) ────────────────────────────────────
        self._bal              = 0.0
        self._net_pl           = 0.0
        self._leverage         = 100.0   # real value loaded from API
        self._total_entry_val  = 0.0     # set by OrderTable every tick
        self._currency         = "USD"
        self._separators       = []

        # ── Theme ────────────────────────────────────────────────────────
        try:
            from Theme.theme_manager import ThemeManager
            mgr = ThemeManager.instance()
            self._apply_container_style(mgr.tokens())
            mgr.theme_changed.connect(lambda name, tok: self._apply_container_style(tok))
            mgr.theme_changed.connect(lambda name, tok: self._refresh_all_labels())
        except Exception:
            self.setStyleSheet(
                "#orders_bottom_bar { background: #F9FAFB; border-top: 1px solid #E5E7EB; }"
            )

        # ── Left container ───────────────────────────────────────────────
        self.content = QWidget(self)
        cl = QHBoxLayout(self.content)
        cl.setContentsMargins(14, 0, 14, 0)
        cl.setSpacing(4)

        self.lbl_currency     = QLabel()
        self.lbl_balance      = QLabel()
        self.lbl_equity       = QLabel()
        self.lbl_margin       = QLabel()
        self.lbl_free_margin  = QLabel()
        self.lbl_margin_level = QLabel()

        def sep():
            s = QLabel("|")
            s.setAlignment(Qt.AlignCenter)
            self._separators.append(s)
            return s

        for i, w in enumerate([
            self.lbl_currency, self.lbl_balance, self.lbl_equity,
            self.lbl_margin, self.lbl_free_margin, self.lbl_margin_level,
        ]):
            cl.addWidget(w)
            if i < 5:
                cl.addWidget(sep())
        cl.addStretch()

        # ── Floating P&L labels ──────────────────────────────────────────
        self.net_pl_title = QLabel(self)
        self.net_pl_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.net_pl_value = QLabel(self)
        self.net_pl_value.setAlignment(Qt.AlignCenter)

        self._refresh_all_labels()

        # ── Table sync ───────────────────────────────────────────────────
        header = self.table_view.horizontalHeader()
        header.sectionResized.connect(self.align_net_pl)
        header.sectionMoved.connect(self.align_net_pl)
        self.table_view.horizontalScrollBar().valueChanged.connect(self.align_net_pl)

        # ── Subscribe to account data ────────────────────────────────────
        try:
            store = AppStore.instance()
            store.account_changed.connect(self._on_account_changed)
            self._on_account_changed(store.get_current_account())
        except Exception:
            pass

        QTimer.singleShot(0, self._initial_layout)
        QTimer.singleShot(10, self.align_net_pl)

    # ── Public setters called by OrderTable ──────────────────────────────

    def set_net_pl(self, value: float):
        """Sum of all open-order P&L — called on every model tick."""
        self._net_pl = float(value)

        color = "#22C55E" if self._net_pl >= 0 else "#EF4444"
        try:
            from Theme.theme_manager import ThemeManager
            tc = ThemeManager.instance().tokens().get("accent", "#1976d2")
        except Exception:
            tc = "#1976d2"

        sign = "+" if self._net_pl >= 0 else ""
        self.net_pl_title.setText(
            f"<span style='color:{tc}; font-size:12px; font-weight:600;'>Net P&L:</span>")
        self.net_pl_value.setText(
            f"<b style='color:{color}; font-size:13px;'>{sign}{self._net_pl:.2f}</b>")

        self._recalculate()

    def set_total_entry_value(self, total_entry_value: float):
        """
        Sum of (entry_price × lot) across all open orders.
        Margin = total_entry_value / account_leverage.
        Leverage is read from the API account object so the division
        uses the real broker leverage, not a hardcoded fallback.
        """
        self._total_entry_val = float(total_entry_value)
        self._recalculate()

    # ── Account changed ──────────────────────────────────────────────────

    def _on_account_changed(self, account_info):
        try:
            store = AppStore.instance()
            self._load_from_account(account_info, store.get_api_response())
        except Exception:
            pass

    def _load_from_account(self, current_account, api_response):
        """
        Reads balance, currency, and leverage from the API account object.
        These are all confirmed present in the API response:
            'balance', 'currency', 'leverage'
        """
        try:
            source = self._find_source(current_account, api_response)
            if source is None:
                return

            # Balance
            self._bal = self._f(
                source.get('balance') or source.get('accountBalance')
            )

            # Currency
            self._currency = (
                source.get('currency') or
                source.get('accountCurrency') or
                "USD"
            )

            # Leverage — confirmed present in API ('leverage' key)
            lev = self._f(
                source.get('leverage') or
                source.get('accountLeverage') or
                source.get('account_leverage')
            )
            if lev > 0:
                self._leverage = lev
            # else keep existing _leverage (default 100)

            self._recalculate()
        except Exception:
            pass

    # ── Core calculation ─────────────────────────────────────────────────

    def _recalculate(self):
        """
        Margin       = total_entry_value / leverage   (backend leverage)
        Equity       = Balance + Net P&L
        Free Margin  = Equity  - Margin
        Margin Level = (Equity / Margin) × 100 %
        """
        margin = self._total_entry_val / self._leverage if self._leverage > 0 else 0.0
        equity = self._bal + self._net_pl
        free   = equity - margin

        margin_level_str = (
            f"{(equity / margin) * 100:,.2f}%"
            if margin > 0 else "0.0"
        )

        # Format and push to labels
        self._show(
            currency     = self._currency,
            balance      = f"{self._bal:,.2f}",
            equity       = f"{equity:,.2f}",
            margin       = f"{margin:,.2f}",
            free_margin  = f"{free:,.2f}",
            margin_level = margin_level_str,
        )

    def _show(self, *, currency, balance, equity, margin, free_margin, margin_level):
        try:
            self.lbl_currency.setText(self._fmt("Currency",     currency))
            self.lbl_balance.setText(self._fmt("Balance",       balance))
            self.lbl_equity.setText(self._fmt("Equity",         equity))
            self.lbl_margin.setText(self._fmt("Margin",         margin))
            self.lbl_free_margin.setText(self._fmt("Free Margin", free_margin))
            self.lbl_margin_level.setText(
                self._fmt("Margin Level", margin_level, "#22C55E"))

            try:
                from Theme.theme_manager import ThemeManager
                sc = ThemeManager.instance().tokens().get("border_separator", "#CBD5E1")
            except Exception:
                sc = "#CBD5E1"
            for s in self._separators:
                s.setStyleSheet(f"color:{sc}; margin-left:22px; margin-right:22px;")
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _f(value, default=0.0):
        try:
            if value is None or str(value).strip() in ("", "None"):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _find_source(self, current_account, api_response):
        """Locate the matching account dict from the API response."""
        all_accounts = []
        if isinstance(api_response, dict):
            all_accounts.extend(api_response.get('accounts') or [])
            for group in (api_response.get('sharedAccounts') or []):
                all_accounts.extend(group.get('accounts') or [])

        target_id = None
        if isinstance(current_account, dict):
            raw = (current_account.get('account_id') or
                   current_account.get('accountId') or
                   current_account.get('id'))
            target_id = str(raw).strip() if raw is not None else None

        # Strategy 1: exact ID match
        if target_id:
            for a in all_accounts:
                cid = str(
                    a.get('accountId') or a.get('account_id') or a.get('id') or ""
                ).strip()
                if cid == target_id:
                    return a

        # Strategy 2: only one account in response
        if len(all_accounts) == 1:
            return all_accounts[0]

        # Strategy 3: current_account itself has balance
        if isinstance(current_account, dict) and current_account.get('balance') is not None:
            return current_account

        return None

    # ── Styling ──────────────────────────────────────────────────────────

    def _apply_container_style(self, tok):
        bg     = tok.get('bg_bottom_bar', '#F9FAFB')
        border = tok.get('border_separator', '#E5E7EB')
        self.setStyleSheet(
            f"#orders_bottom_bar {{ background: {bg}; border-top: 1px solid {border}; }}"
        )

    def _fmt(self, title, value, value_color=None):
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            ct  = tok.get("accent", "#1976d2")
            cv  = value_color or tok.get("text_primary", "#1F2937")
        except Exception:
            ct = "#1976d2"
            cv = value_color or "#1F2937"
        return (
            f"<span style='color:{ct}; font-size:13px; font-weight:600;'>{title}:</span>"
            f"&nbsp;&nbsp;&nbsp;<b style='color:{cv}; font-size:13px;'>{value}</b>"
        )

    def _refresh_all_labels(self):
        """Re-render labels using current state (called on theme change)."""
        self._recalculate()

    # ── Net P&L column alignment ─────────────────────────────────────────

    def align_net_pl(self, *args):
        try:
            header = self.table_view.horizontalHeader()
            if header.isSectionHidden(self.profit_col_index):
                self.net_pl_title.hide()
                self.net_pl_value.hide()
                return

            visual_idx = header.visualIndex(self.profit_col_index)
            viewport_x = header.sectionViewportPosition(visual_idx)
            col_width  = header.sectionSize(visual_idx)
            v_w = (self.table_view.verticalHeader().width()
                   if self.table_view.verticalHeader().isVisible() else 0)
            final_x = viewport_x + v_w

            if final_x < self.lbl_margin_level.geometry().right() + 40:
                self.net_pl_title.hide()
            else:
                self.net_pl_title.show()
                self.net_pl_title.setGeometry(final_x - 105, 0, 100, self.height())

            self.net_pl_value.show()
            self.net_pl_value.setGeometry(final_x, 0, col_width, self.height())
        except Exception:
            pass

    # ── Qt overrides ─────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.content.resize(self.width(), self.height())
        self.align_net_pl()

    def _initial_layout(self):
        self.content.setFixedHeight(self.height())
        self.content.move(0, 0)
        self.align_net_pl()

class HistoryBottomBar(QWidget):
    """
    Bottom summary bar for the History table.

    Left side (static HBox):
        Account Currency | Deposits | Withdrawals

    Right side (floating, absolutely positioned over columns):
        Comm     — aligned to COMMISSION column
        Swap     — aligned to SWAP column
        Net P&L  — aligned to PROFIT/LOSS column

    Constructor:
        HistoryBottomBar(table_view, col_map, parent=self)
        col_map = {'commission': idx, 'swap': idx, 'pl': idx}
    """

    def __init__(self, table_view, col_map: dict, parent=None):
        super().__init__(parent)
        self.table_view = table_view
        self.col_map    = col_map          # {key: logical_col_index}
        self.setFixedHeight(32)
        self.setObjectName("history_bottom_bar")

        # ── Raw state ────────────────────────────────────────────────────
        self._currency    = "USD"
        self._deposits    = 0.0
        self._withdrawals = 0.0
        self._comm        = 0.0
        self._swap        = 0.0
        self._net_pl      = 0.0
        self._separators  = []

        # ── Theme ────────────────────────────────────────────────────────
        try:
            from Theme.theme_manager import ThemeManager
            mgr = ThemeManager.instance()
            self._apply_container_style(mgr.tokens())
            mgr.theme_changed.connect(lambda name, tok: self._apply_container_style(tok))
            mgr.theme_changed.connect(lambda name, tok: self._refresh_all_labels())
        except Exception:
            self.setStyleSheet(
                "#history_bottom_bar { background: #F9FAFB; border-top: 1px solid #E5E7EB; }"
            )

        # ── Static left container (Currency | Deposits | Withdrawals) ────
        self.content = QWidget(self)
        cl = QHBoxLayout(self.content)
        cl.setContentsMargins(14, 0, 14, 0)
        cl.setSpacing(4)

        self._static_seps = []   # left-side separators styled independently

        def _sep():
            s = QLabel("|")
            s.setAlignment(Qt.AlignCenter)
            self._separators.append(s)
            self._static_seps.append(s)
            return s

        self.lbl_currency    = QLabel()
        self.lbl_deposits    = QLabel()
        self.lbl_withdrawals = QLabel()

        cl.addWidget(self.lbl_currency)
        cl.addWidget(_sep()); cl.addWidget(self.lbl_deposits)
        cl.addWidget(_sep()); cl.addWidget(self.lbl_withdrawals)
        cl.addStretch()

        # ── Floating labels (absolutely positioned over columns) ──────────
        self.lbl_comm    = QLabel(self)
        self.lbl_swap    = QLabel(self)
        self.lbl_net_pl  = QLabel(self)
        for lbl in (self.lbl_comm, self.lbl_swap, self.lbl_net_pl):
            lbl.setAlignment(Qt.AlignCenter)

        # Re-align whenever column geometry changes
        header = self.table_view.horizontalHeader()
        header.sectionResized.connect(self._align_floating_labels)
        header.sectionMoved.connect(self._align_floating_labels)
        self.table_view.horizontalScrollBar().valueChanged.connect(self._align_floating_labels)

        # ── Subscribe to account data ─────────────────────────────────────
        try:
            store = AppStore.instance()
            store.account_changed.connect(self._on_account_changed)
            self._on_account_changed(store.get_current_account())
        except Exception:
            pass

        self._refresh_all_labels()
        QTimer.singleShot(0,  self._initial_layout)
        QTimer.singleShot(10, self._align_floating_labels)

    # ── Public setters ───────────────────────────────────────────────────

    def set_currency(self, currency: str):
        self._currency = currency or "USD"
        self._refresh_all_labels()

    def set_deposits(self, value: float):
        self._deposits = float(value)
        self._refresh_all_labels()

    def set_withdrawals(self, value: float):
        self._withdrawals = float(value)
        self._refresh_all_labels()

    def set_commission(self, value: float):
        self._comm = float(value)
        self._refresh_all_labels()

    def set_swap(self, value: float):
        self._swap = float(value)
        self._refresh_all_labels()

    def set_net_pl(self, value: float):
        self._net_pl = float(value)
        self._refresh_all_labels()

    # ── Column-visibility mirror ──────────────────────────────────────────

    def show_column_label(self, col_key: str, visible: bool):
        mapping = {"commission": self.lbl_comm,
                   "swap":       self.lbl_swap,
                   "pl":         self.lbl_net_pl}
        lbl = mapping.get(col_key)
        if lbl:
            lbl.setVisible(visible)

    def sync_to_header(self, header, col_map: dict):
        for col_key in ("commission", "swap", "pl"):
            idx = col_map.get(col_key, -1)
            if idx >= 0:
                self.show_column_label(col_key, not header.isSectionHidden(idx))
        self._align_floating_labels()

    # ── Floating label positioning ────────────────────────────────────────

    def _align_floating_labels(self, *args):
        try:
            header = self.table_view.horizontalHeader()
            v_w = (self.table_view.verticalHeader().width()
                   if self.table_view.verticalHeader().isVisible() else 0)
            h = self.height()

            for col_key, lbl in (("commission", self.lbl_comm),
                                  ("swap",       self.lbl_swap),
                                  ("pl",         self.lbl_net_pl)):
                col_idx = self.col_map.get(col_key, -1)
                if col_idx < 0:
                    lbl.hide()
                    continue

                if header.isSectionHidden(col_idx):
                    lbl.hide()
                    continue

                visual_idx = header.visualIndex(col_idx)
                vp_x       = header.sectionViewportPosition(visual_idx)
                col_w      = header.sectionSize(visual_idx)

                if vp_x < 0:          # scrolled off left
                    lbl.hide()
                    continue

                lbl.show()
                lbl.setGeometry(v_w + vp_x, 0, col_w, h)
        except Exception:
            pass

    # ── Account change handler ────────────────────────────────────────────

    def _on_account_changed(self, account_info):
        try:
            store    = AppStore.instance()
            api_resp = store.get_api_response()
            all_accs = []
            if isinstance(api_resp, dict):
                all_accs.extend(api_resp.get('accounts') or [])
                for g in (api_resp.get('sharedAccounts') or []):
                    all_accs.extend(g.get('accounts') or [])

            source = None
            if isinstance(account_info, dict):
                raw = (account_info.get('account_id') or
                       account_info.get('accountId') or
                       account_info.get('id'))
                tid = str(raw).strip() if raw is not None else None
                for a in all_accs:
                    cid = str(
                        a.get('accountId') or a.get('account_id') or a.get('id') or ""
                    ).strip()
                    if tid and cid == tid:
                        source = a
                        break
            if source is None and len(all_accs) == 1:
                source = all_accs[0]
            if source is None and isinstance(account_info, dict):
                source = account_info

            if source:
                self._currency = (
                    source.get('currency') or
                    source.get('accountCurrency') or
                    "USD"
                )
                self._refresh_all_labels()
        except Exception:
            pass

    # ── Rendering ────────────────────────────────────────────────────────

    def _refresh_all_labels(self):
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            ct  = tok.get("accent",           "#1976d2")
            cv  = tok.get("text_primary",      "#1F2937")
            sc  = tok.get("border_separator",  "#CBD5E1")
        except Exception:
            ct, cv, sc = "#1976d2", "#1F2937", "#CBD5E1"

        def _fmt(title, value, vc=None):
            c = vc or cv
            return (
                f"<span style='color:{ct}; font-size:13px; font-weight:600;'>{title}:</span>"
                f"&nbsp;&nbsp;&nbsp;<b style='color:{c}; font-size:13px;'>{value}</b>"
            )

        w_color    = "#EF4444" if self._withdrawals < 0 else cv
        swap_color = "#EF4444" if self._swap        < 0 else cv
        pl_color   = "#22C55E" if self._net_pl     >= 0 else "#EF4444"
        sign       = "+" if self._net_pl >= 0 else ""

        self.lbl_currency.setText(   _fmt("Account Currency", self._currency))
        self.lbl_deposits.setText(   _fmt("Deposits",         f"{self._deposits:,.2f}"))
        self.lbl_withdrawals.setText(_fmt("Withdrawals",      f"{self._withdrawals:,.2f}", w_color))

        self.lbl_comm.setText(  _fmt("Comm",    f"{self._comm:,.2f}"))
        self.lbl_swap.setText(  _fmt("Swap",    f"{self._swap:,.2f}", swap_color))
        self.lbl_net_pl.setText(_fmt("Net P&L", f"{sign}{self._net_pl:,.2f}", pl_color))

        for s in self._separators:
            if s in self._static_seps:
                s.setStyleSheet(f"color:{sc}; margin-left:32px; margin-right:32px;")
            else:
                s.setStyleSheet(f"color:{sc}; margin-left:22px; margin-right:22px;")

        self._align_floating_labels()

    # ── Style ────────────────────────────────────────────────────────────

    def _apply_container_style(self, tok):
        bg     = tok.get('bg_bottom_bar', '#F9FAFB')
        border = tok.get('border_separator', '#E5E7EB')
        self.setStyleSheet(
            f"#history_bottom_bar {{ background: {bg}; border-top: 1px solid {border}; }}"
        )

    # ── Qt overrides ─────────────────────────────────────────────────────

    def _initial_layout(self):
        self.content.setFixedHeight(self.height())
        self.content.move(0, 0)
        self._align_floating_labels()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.content.resize(self.width(), self.height())
        self._align_floating_labels()