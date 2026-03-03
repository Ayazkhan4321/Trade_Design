from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QHeaderView, QComboBox, QCheckBox, QDoubleSpinBox, QWidget, QFrame, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QPoint
import logging
import requests

from api.config import API_ORDERS_BULK_CLOSE, API_TIMEOUT, API_VERIFY_TLS
import auth.session as session

LOG = logging.getLogger(__name__)


class BulkCloseDialog(QDialog):
    """Simple modal to select multiple orders and POST to bulk-close endpoint.

    Minimal UI: a table of orders with checkboxes and a Close button.
    The dialog expects either an `order_service` (preferred) or a `model`
    (OrderModel) to read the currently shown orders.
    """

    def __init__(self, parent=None, order_service=None, model=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setWindowTitle("Bulk Close Orders")
        self.resize(640, 480)
        self.order_service = order_service
        self.model = model or (getattr(order_service, 'model', None) if order_service is not None else None)

        self._drag_pos = None

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_container)

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(0, 0, 0, 15)
        layout.setSpacing(12)

        # Header (dark blue) with larger title and subtitle
        self.header_widget = QWidget(self)
        self.header_widget.setObjectName("HeaderWidget")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        icon = QLabel("\U0001F4E6")
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        icon.setFixedWidth(28)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_label = QLabel("Bulk Close Orders")
        self.title_label.setObjectName("HeaderTitle")
        self.subtitle = QLabel("Configure filters and close multiple orders at once")
        self.subtitle.setObjectName("HeaderSubtitle")
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.subtitle)
        
        self.btn_x_close = QPushButton("✕")
        self.btn_x_close.setObjectName("HeaderCloseBtn")
        self.btn_x_close.setFixedSize(36, 36) 
        self.btn_x_close.setCursor(Qt.PointingHandCursor)
        self.btn_x_close.clicked.connect(self.reject)
        
        header_layout.addWidget(icon)
        header_layout.addLayout(text_col)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_x_close)
        
        layout.addWidget(self.header_widget)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(16, 0, 16, 0)

        # Top controls: Symbol selector | Order Type (equal width)
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Symbol"))
        self.symbol_combo = QComboBox(self)
        self.symbol_combo.addItem("All Symbols")
        self.symbol_combo.currentIndexChanged.connect(self._apply_filters)
        left.addWidget(self.symbol_combo)
        top.addLayout(left, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Order Type"))
        self.order_type = QComboBox(self)
        self.order_type.addItem("All")
        self.order_type.addItem("Buy")
        self.order_type.addItem("Sell")
        self.order_type.currentIndexChanged.connect(self._apply_filters)
        right.addWidget(self.order_type)
        top.addLayout(right, 1)

        content_layout.addLayout(top)

        # Make dialog body a light-blue background (Now handled by dynamic ThemeManager)

        # Profit / Loss filter row (two equal blocks)
        pf_row = QHBoxLayout()
        # Profit block (contained)
        profit_block = QHBoxLayout()
        self.profit_check = QCheckBox("Profit >", self)
        self.profit_val = QDoubleSpinBox(self)
        self.profit_val.setMaximum(9999999.0)
        self.profit_val.setDecimals(2)
        profit_block.addWidget(self.profit_check)
        profit_block.addWidget(self.profit_val)
        self.profit_check.stateChanged.connect(self._apply_filters)
        self.profit_val.valueChanged.connect(self._apply_filters)
        self.profit_container = QWidget(self)
        self.profit_container.setObjectName("FilterBox")
        self.profit_container.setLayout(profit_block)
        pf_row.addWidget(self.profit_container, 1)

        # Loss block (contained)
        loss_block = QHBoxLayout()
        self.loss_check = QCheckBox("Loss >", self)
        self.loss_val = QDoubleSpinBox(self)
        self.loss_val.setMaximum(9999999.0)
        self.loss_val.setDecimals(2)
        loss_block.addWidget(self.loss_check)
        loss_block.addWidget(self.loss_val)
        self.loss_check.stateChanged.connect(self._apply_filters)
        self.loss_val.valueChanged.connect(self._apply_filters)
        self.loss_container = QWidget(self)
        self.loss_container.setObjectName("FilterBox")
        self.loss_container.setLayout(loss_block)
        pf_row.addWidget(self.loss_container, 1)

        content_layout.addLayout(pf_row)

        # Count / select all row
        info_row = QHBoxLayout()
        self.select_all = QCheckBox("", self)
        self.select_all.stateChanged.connect(self._on_select_all)
        info_row.addWidget(self.select_all)
        self.count_label = QLabel("0 ORDERS FOUND")
        self.count_label.setStyleSheet("font-weight: bold;")
        info_row.addWidget(self.count_label)
        info_row.addStretch()
        content_layout.addLayout(info_row)

        # Table view backed by a QStandardItemModel for checkboxes
        self.view = QTableView(self)
        self.view.setObjectName("BulkTable")
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.NoSelection)
        self.view.verticalHeader().setVisible(False)

        # Table columns: checkbox, Symbol, ID, Type, Lot, Entry, SL, TP, Profit/Loss
        self.table_model = QStandardItemModel(0, 9, self)
        self.table_model.setHorizontalHeaderLabels(["", "Symbol", "ID", "Type", "Lot", "Entry", "SL", "TP", "Profit/Loss"])
        self.view.setModel(self.table_model)
        header = self.view.horizontalHeader()
        for i in range(9):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        content_layout.addWidget(self.view)

        # Footer: only main Close button centered and styled
        footer = QHBoxLayout()
        footer.addStretch()
        self.close_btn = QPushButton("Close 0 Orders")
        self.close_btn.setObjectName("ActionBtn")
        self.close_btn.setMinimumHeight(38)
        self.close_btn.setMinimumWidth(180)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        footer.addWidget(self.close_btn)
        footer.addStretch()
        content_layout.addLayout(footer)

        layout.addLayout(content_layout)

        self.close_btn.clicked.connect(self._on_close)

        self._apply_theme()
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(lambda n, t: self._apply_theme())
        except Exception:
            pass

        self._populate()
        self._update_count_and_button()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.header_widget.geometry().contains(event.pos()):
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _apply_theme(self):
        try:
            from Theme.theme_manager import ThemeManager
            tok = ThemeManager.instance().tokens()
            bg_panel = tok.get("bg_panel", "#ffffff")
            text_pri = tok.get("text_primary", "#1a202c")
            text_sec = tok.get("text_secondary", "#4a5568")
            border = tok.get("border_primary", "#e5e7eb")
            bg_input = tok.get("bg_input", "#f5f7fa")
            accent = tok.get("accent", "#1976d2")
            is_dark = tok.get("is_dark", "false") == "true"
            
            acc_t = "#ffffff" if is_dark else tok.get("accent_text", "#ffffff")
            if "crazy" in ThemeManager.instance().current_theme or not is_dark:
                acc_t = "#ffffff"
        except Exception:
            bg_panel, text_pri, text_sec, border, accent, bg_input, acc_t, is_dark = (
                "#ffffff", "#1a202c", "#4a5568", "#e5e7eb", "#1976d2", "#f5f7fa", "#ffffff", False
            )

        if is_dark:
            if border == "#e5e7eb": border = "#374151"
            if bg_input == "#f5f7fa": bg_input = "#1f2937"

        self.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {bg_panel};
                border: 2px solid {accent};
                border-radius: 8px;
            }}
            QWidget#HeaderWidget {{
                background-color: {accent};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QLabel#HeaderTitle {{
                color: {acc_t};
                font-size: 16px;
                font-weight: 700;
                background: transparent;
            }}
            QLabel#HeaderSubtitle {{
                color: {acc_t};
                font-size: 12px;
                background: transparent;
                opacity: 0.85;
            }}
            QPushButton#HeaderCloseBtn {{
                background: transparent;
                border: none;
                color: {acc_t};
                font-size: 20px;  
                font-weight: bold;
            }}
            QPushButton#HeaderCloseBtn:hover {{
                background: rgba(0, 0, 0, 0.15);
                border-radius: 18px;
            }}
            QLabel {{
                color: {text_pri};
            }}
            QWidget#FilterBox {{
                background-color: {bg_input};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QComboBox, QDoubleSpinBox {{
                background-color: {bg_input};
                color: {text_pri};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px;
            }}
            QCheckBox {{
                color: {text_pri};
            }}
            QTableView#BulkTable {{
                background-color: {bg_input};
                color: {text_pri};
                border: 1px solid {border};
                gridline-color: {border};
            }}
            QHeaderView::section {{
                background-color: {bg_panel};
                color: {text_pri};
                border: 1px solid {border};
                padding: 4px;
                font-weight: bold;
            }}
            QPushButton#ActionBtn {{
                background-color: {accent};
                color: {acc_t};
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton#ActionBtn:hover {{
                background-color: {accent};
                opacity: 0.85;
            }}
        """)

    def _populate(self):
        # Populate from model.orders if available
        rows = []
        try:
            if self.model is not None and hasattr(self.model, 'orders'):
                rows = list(self.model.orders)
            elif self.order_service is not None and callable(getattr(self.order_service, 'get_active_orders', None)):
                rows = self.order_service.get_active_orders()
        except Exception:
            LOG.exception("Failed to retrieve orders for bulk close")

        self.table_model.setRowCount(0)
        seen_symbols = set()
        for o in rows:
            try:
                chk = QStandardItem("")
                chk.setCheckable(True)
                chk.setEditable(False)
                sym_text = str(o.get('symbol') or o.get('Symbol') or '')
                sym = QStandardItem(sym_text)
                sym.setEditable(False)
                oid_text = str(o.get('id') or o.get('orderId') or o.get('ID') or '')
                oid = QStandardItem(oid_text)
                oid.setEditable(False)
                typ = QStandardItem(str(o.get('type') or o.get('orderType') or ''))
                typ.setEditable(False)
                lot = QStandardItem(str(o.get('lot') or o.get('lotSize') or ''))
                lot.setEditable(False)
                entry = QStandardItem(str(o.get('entry_price') or o.get('entryPrice') or ''))
                entry.setEditable(False)
                sl = QStandardItem(str(o.get('sl') or o.get('stopLoss') or '-'))
                sl.setEditable(False)
                tp = QStandardItem(str(o.get('tp') or o.get('takeProfit') or '-'))
                tp.setEditable(False)
                # Profit/Loss may exist as 'pl' on the order dict
                pl_val = o.get('pl')
                try:
                    pl_txt = f"{float(pl_val):.2f}" if pl_val is not None else "0.00"
                except Exception:
                    pl_txt = str(pl_val or "0.00")
                pl = QStandardItem(pl_txt)
                pl.setEditable(False)
                self.table_model.appendRow([chk, sym, oid, typ, lot, entry, sl, tp, pl])
                try:
                    s = sym_text
                    if s:
                        seen_symbols.add(s)
                except Exception:
                    pass
            except Exception:
                pass

        # Populate symbol combo with discovered symbols
        try:
            current = self.symbol_combo.currentText()
            self.symbol_combo.blockSignals(True)
            self.symbol_combo.clear()
            self.symbol_combo.addItem("All Symbols")
            for s in sorted(seen_symbols):
                self.symbol_combo.addItem(s)
            # restore selection if possible
            idx = self.symbol_combo.findText(current) if current else 0
            self.symbol_combo.setCurrentIndex(idx if idx != -1 else 0)
            self.symbol_combo.blockSignals(False)
        except Exception:
            pass

        self._update_count_and_button()

    def _selected_order_ids(self):
        ids = []
        for r in range(self.table_model.rowCount()):
            try:
                itm = self.table_model.item(r, 0)
                if itm is not None and itm.checkState() == Qt.Checked:
                    id_item = self.table_model.item(r, 2)
                    if id_item is not None:
                        ids.append(id_item.text())
            except Exception:
                pass
        return ids

    def _on_select_all(self, state):
        checked = state == Qt.Checked
        for r in range(self.table_model.rowCount()):
            try:
                itm = self.table_model.item(r, 0)
                if itm is not None:
                    itm.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            except Exception:
                pass
        self._update_count_and_button()

    def _apply_filters(self):
        # Filtering: symbol, order type, profit and loss
        sym = self.symbol_combo.currentText() if self.symbol_combo.currentIndex() >= 0 else "All Symbols"
        order_type = self.order_type.currentText() if self.order_type.currentIndex() >= 0 else "All"
        profit_active = getattr(self, 'profit_check', None) and self.profit_check.isChecked()
        profit_val = float(self.profit_val.value()) if profit_active else None
        loss_active = getattr(self, 'loss_check', None) and self.loss_check.isChecked()
        loss_val = float(self.loss_val.value()) if loss_active else None
        
        for r in range(self.table_model.rowCount()):
            try:
                # columns: 0 chk,1 sym,2 id,3 type,8 pl
                sym_item = self.table_model.item(r, 1)
                type_item = self.table_model.item(r, 3)
                pl_item = self.table_model.item(r, 8)
                visible = True
                if sym and sym != "All Symbols":
                    visible = (sym_item.text() == sym)
                if visible and order_type and order_type != "All":
                    visible = (type_item.text().strip().lower() == order_type.strip().lower())
                if visible and profit_active:
                    try:
                        plv = float(pl_item.text())
                        visible = (plv >= profit_val)
                    except Exception:
                        visible = False
                if visible and loss_active:
                    try:
                        plv = float(pl_item.text())
                        visible = (plv <= -abs(loss_val))
                    except Exception:
                        visible = False
                self.view.setRowHidden(r, not visible)
            except Exception:
                pass
        self._update_count_and_button()

    def _update_count_and_button(self):
        total = 0
        selected = 0
        types_seen = set()
        for r in range(self.table_model.rowCount()):
            try:
                if self.view.isRowHidden(r):
                    continue
                total += 1
                itm = self.table_model.item(r, 0)
                if itm is not None and itm.checkState() == Qt.Checked:
                    selected += 1
                try:
                    t = self.table_model.item(r, 3)
                    if t is not None:
                        types_seen.add(t.text())
                except Exception:
                    pass
            except Exception:
                pass
        self.count_label.setText(f"{total} ORDERS FOUND")
        # Build button label: prefer specific type if only one type visible
        label_count = selected if selected > 0 else total
        type_label = ""
        if len(types_seen) == 1:
            type_label = f" {list(types_seen)[0]}"
        btn_text = f"Close {label_count}{type_label} Orders"
        try:
            self.close_btn.setText(btn_text)
            self.close_btn.setEnabled(selected > 0)
        except Exception:
            pass

    def _on_close(self):
        ids = self._selected_order_ids()
        if not ids:
            LOG.info("No orders selected for bulk close")
            return

        self.close_btn.setEnabled(False)
        self.close_btn.setText("Closing Orders...")

        # Safely convert to strict integers for the server payload
        clean_ids = []
        for i in ids:
            try:
                clean_ids.append(int(float(i)))
            except Exception:
                clean_ids.append(i)

        payload = {"orderIds": clean_ids}
        headers = {}
        token = session.get_token()
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        try:
            LOG.debug("Posting bulk close payload: %s", payload)
            resp = requests.post(API_ORDERS_BULK_CLOSE, json=payload, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            LOG.info("Bulk close status: %s", getattr(resp, 'status_code', None))
            
            # Accept ALL 2xx success codes (200, 201, 202, 204)
            if resp is not None and (200 <= resp.status_code < 300):
                QMessageBox.information(self, "Success", f"Successfully closed {len(ids)} orders.")
                
                # Refresh orders via service if available
                try:
                    if self.order_service is not None and callable(getattr(self.order_service, 'fetch_orders', None)):
                        new = self.order_service.fetch_orders()
                        if self.model is not None and hasattr(self.model, 'clear_orders'):
                            try:
                                self.model.clear_orders()
                                for o in new:
                                    try:
                                        self.model.add_order(o)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    LOG.exception("Failed refreshing orders after bulk close")
                self.accept()
            else:
                status_code = getattr(resp, 'status_code', 'Unknown')
                try:
                    LOG.error("Bulk close failed: %s", resp.text)
                except Exception:
                    pass
                QMessageBox.warning(self, "Action Failed", f"Backend rejected the request.\nStatus: {status_code}")
                self.close_btn.setEnabled(True)
                self.close_btn.setText(f"Close {len(ids)} Orders")
                
        except Exception as e:
            LOG.exception("Exception while calling bulk close endpoint")
            QMessageBox.critical(self, "Error", f"Failed to connect to the server:\n{e}")
            self.close_btn.setEnabled(True)
            self.close_btn.setText(f"Close {len(ids)} Orders")