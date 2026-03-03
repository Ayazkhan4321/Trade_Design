from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QHeaderView, QComboBox, QCheckBox, QDoubleSpinBox, QWidget
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
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
        self.setWindowTitle("Bulk Close Orders")
        self.resize(640, 420)
        self.order_service = order_service
        self.model = model or (getattr(order_service, 'model', None) if order_service is not None else None)

        layout = QVBoxLayout(self)

        # Header (dark blue) with larger title and subtitle
        try:
            header_widget = QWidget(self)
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(12, 10, 12, 10)
            icon = QLabel("\U0001F4E6")
            icon.setFixedWidth(28)
            title_label = QLabel("Bulk Close Orders")
            title_label.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
            subtitle = QLabel("Configure filters and close multiple orders at once")
            subtitle.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px;")
            text_col = QVBoxLayout()
            text_col.addWidget(title_label)
            text_col.addWidget(subtitle)
            header_layout.addWidget(icon)
            header_layout.addLayout(text_col)
            header_widget.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b8ef6, stop:1 #1e63d6); border-top-left-radius:6px; border-top-right-radius:6px;")
            layout.addWidget(header_widget)
        except Exception:
            pass

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

        layout.addLayout(top)

        # Make dialog body a light-blue background
        try:
            self.setStyleSheet("background-color: #eaf4ff;")
        except Exception:
            pass

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
        profit_container = QWidget(self)
        profit_container.setLayout(profit_block)
        profit_container.setStyleSheet("background: white; border: 1px solid #cfd8e3; border-radius:6px; padding:6px;")
        pf_row.addWidget(profit_container, 1)

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
        loss_container = QWidget(self)
        loss_container.setLayout(loss_block)
        loss_container.setStyleSheet("background: white; border: 1px solid #cfd8e3; border-radius:6px; padding:6px;")
        pf_row.addWidget(loss_container, 1)

        layout.addLayout(pf_row)

        # Count / select all row
        info_row = QHBoxLayout()
        self.select_all = QCheckBox("", self)
        self.select_all.stateChanged.connect(self._on_select_all)
        info_row.addWidget(self.select_all)
        self.count_label = QLabel("0 ORDERS FOUND")
        info_row.addWidget(self.count_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        # Table view backed by a QStandardItemModel for checkboxes
        self.view = QTableView(self)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.NoSelection)
        self.view.verticalHeader().setVisible(False)

        # Table columns: checkbox, Symbol, ID, Type, Lot, Entry, SL, TP, Profit/Loss
        self.table_model = QStandardItemModel(0, 9, self)
        self.table_model.setHorizontalHeaderLabels(["", "Symbol", "ID", "Type", "Lot", "Entry", "SL", "TP", "Profit/Loss"])
        self.view.setModel(self.table_model)
        header = self.view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)

        layout.addWidget(self.view)

        # Footer: only main Close button centered and styled
        footer = QHBoxLayout()
        footer.addStretch()
        self.close_btn = QPushButton("Close 0 Orders")
        try:
            self.close_btn.setMinimumHeight(36)
            self.close_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b8ef6, stop:1 #1e63d6); color: white; padding: 10px; border-radius: 8px; font-size: 14px; font-weight: 600;")
        except Exception:
            pass
        footer.addWidget(self.close_btn)
        footer.addStretch()
        layout.addLayout(footer)

        self.close_btn.clicked.connect(self._on_close)

        self._populate()
        self._update_count_and_button()

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
                LOG.exception("Failed adding order row to bulk close dialog: %s", o)

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
                        try:
                            ids.append(int(id_item.text()))
                        except Exception:
                            ids.append(id_item.text())
            except Exception:
                LOG.exception("Failed reading selected id at row %s", r)
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
        except Exception:
            pass
    def _on_close(self):
            ids = self._selected_order_ids()
            if not ids:
                LOG.info("No orders selected for bulk close")
                return
    
            payload = {"orderIds": ids}
            headers = {}
            token = session.get_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
            try:
                LOG.debug("Posting bulk close payload: %s", payload)
                resp = requests.post(API_ORDERS_BULK_CLOSE, json=payload, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
                LOG.info("Bulk close status: %s", getattr(resp, 'status_code', None))
                if resp.status_code in (200, 201):
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
                    try:
                        LOG.error("Bulk close failed: %s", resp.text)
                    except Exception:
                        LOG.exception("Bulk close failed")
            except Exception:
                LOG.exception("Exception while calling bulk close endpoint")