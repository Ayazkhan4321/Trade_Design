from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent
from accounts.store import AppStore
from decimal import Decimal, InvalidOperation

class BottomBar(QWidget):
    def __init__(self, table_view, profit_col_index):
        super().__init__()
        self.table_view = table_view
        self.profit_col_index = profit_col_index
        self.setFixedHeight(28)
        self.setObjectName("orders_bottom_bar")

        # --- State variables ---
        self._val_balance = "1,000,000"
        self._val_equity = "1,000,000"
        self._val_margin = "207.51"
        self._val_free_margin = "999,999,792"
        self._val_margin_level = "16,810,628.4"
        self._val_currency = "USD"
        self._val_net_pl = 0.51
        self._separators = []

        # --- Theme Styling ---
        try:
            from Theme.theme_manager import ThemeManager
            mgr = ThemeManager.instance()
            t = mgr.tokens()
            self._apply_container_style(t)
            mgr.theme_changed.connect(lambda name, tok: self._apply_container_style(tok))
            mgr.theme_changed.connect(lambda name, tok: self._refresh_all_labels())
        except Exception:
            self.setStyleSheet("#orders_bottom_bar { background: #F9FAFB; border-top: 1px solid #E5E7EB; }")

        # --- Left side container ---
        self.content = QWidget(self)
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(10, 0, 10, 0)
        content_layout.setSpacing(8)

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

        # --- Floating P&L Labels ---
        self.net_pl_title = QLabel(self)
        self.net_pl_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.net_pl_value = QLabel(self)
        self.net_pl_value.setAlignment(Qt.AlignCenter) 

        self._refresh_all_labels()

        header = self.table_view.horizontalHeader()
        header.sectionResized.connect(self.align_net_pl)
        header.sectionMoved.connect(self.align_net_pl)
        self.table_view.horizontalScrollBar().valueChanged.connect(self.align_net_pl)

        QTimer.singleShot(0, self._initial_layout)
        QTimer.singleShot(10, self.align_net_pl)

    def _apply_container_style(self, tok):
        bg = tok.get('bg_bottom_bar', '#F9FAFB')
        border = tok.get('border_separator', '#E5E7EB')
        self.setStyleSheet(f"#orders_bottom_bar {{ background: {bg}; border-top: 1px solid {border}; }}")

    def align_net_pl(self, *args):
        try:
            header = self.table_view.horizontalHeader()
            if header.isSectionHidden(self.profit_col_index):
                self.net_pl_title.hide()
                self.net_pl_value.hide()
                return

            visual_idx = header.visualIndex(self.profit_col_index)
            viewport_x = header.sectionViewportPosition(visual_idx)
            col_width = header.sectionSize(visual_idx)
            v_header_w = self.table_view.verticalHeader().width() if self.table_view.verticalHeader().isVisible() else 0
            final_x = viewport_x + v_header_w

            metrics_end = self.margin_level.geometry().right() + 40
            if final_x < metrics_end:
                self.net_pl_title.hide()
            else:
                self.net_pl_title.show()
                title_w = 80
                self.net_pl_title.setGeometry(final_x - title_w - 5, 0, title_w, self.height())

            self.net_pl_value.show()
            self.net_pl_value.setGeometry(final_x, 0, col_width, self.height())
        except Exception: pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.content.resize(self.width(), self.height())
        self.align_net_pl()

    def _initial_layout(self):
        self.content.setFixedHeight(self.height())
        self.content.move(0, 0)
        self.align_net_pl()

    def _format_label(self, title, value, value_color=None):
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            color_title = tok.get("accent", "#1976d2") 
            if not value_color:
                value_color = tok.get("text_primary", "#1F2937")
        except Exception:
            color_title = "#1976d2"
            value_color = value_color or "#1F2937"
            
        return f"<span style='color:{color_title}; font-size:12px; font-weight:600;'>{title}:</span> &nbsp;<b style='color:{value_color}; font-size:12px;'>{value}</b>"

    def _refresh_all_labels(self):
        try:
            self.currency.setText(self._format_label("Currency", self._val_currency))
            self.balance.setText(self._format_label("Balance", self._val_balance))
            self.equity.setText(self._format_label("Equity", self._val_equity))
            self.margin.setText(self._format_label("Margin", self._val_margin))
            self.free_margin.setText(self._format_label("Free Margin", self._val_free_margin))
            self.margin_level.setText(self._format_label("Margin Level", self._val_margin_level, "#22C55E"))
            self.set_net_pl(self._val_net_pl) 
            
            try:
                from Theme.theme_manager import ThemeManager
                sep_c = ThemeManager.instance().tokens().get("border_separator", "#CBD5E1")
            except Exception: sep_c = "#CBD5E1"
            
            for s in self._separators:
                s.setStyleSheet(f"color: {sep_c}; margin-left:6px; margin-right:6px;")
        except Exception: pass

    def set_net_pl(self, value):
        self._val_net_pl = value
        color = "#22C55E" if value >= 0 else "#EF4444"
        try:
            from Theme.theme_manager import ThemeManager
            title_color = ThemeManager.instance().tokens().get("accent", "#1976d2")
        except Exception: title_color = "#1976d2"
        self.net_pl_title.setText(f"<span style='color:{title_color}; font-size:12px; font-weight:600;'>Net P&L:</span>")
        self.net_pl_value.setText(f"<b style='color:{color}; font-size:13px;'>{'+' if value >= 0 else ''}{value:.2f}</b>")