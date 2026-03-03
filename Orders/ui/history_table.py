from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt


class HistoryTable(QWidget):
    """Simple, scrollable inbox table for messages/logs related to orders.

    Designed to be lightweight and follow the app's pattern: expose a
    widget with a `set_rows(list[dict])` API so callers can populate data
    from network responses or local stores.
    """

    COLUMNS = [
        ("id", "ID"),
        ("time", "TIME"),
        ("type", "TYPE"),
        ("symbol", "SYMBOL"),
        ("lot", "LOT SIZE"),
        ("entry_price", "ENTRY PRICE"),
        ("entry_value", "ENTRY VALUE"),
        ("sl", "S/L"),
        ("tp", "T/P"),
        ("closed_time", "CLOSED TIME"),
        ("closed_price", "CLOSED PRICE"),
        ("closed_value", "CLOSED VALUE"),
        ("commission", "COMMISSION"),
        ("swap", "SWAP"),
        ("pl", "PROFIT/LOSS"),
        ("pl_pct", "P/L IN %"),
        ("remarks", "REMARK"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = QTableView(self)
        self.view.setObjectName("inbox_table_view")
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.SingleSelection)
        self.view.verticalHeader().setVisible(False)
        self.view.setAlternatingRowColors(True)

        # Disable hover and use theme-driven selection colour
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            self.view.setStyleSheet(
                f"QTableView::item:hover {{ background: {t['bg_row_hover']}; }}"
                f"QTableView::item:selected {{ background: {t['bg_selected']}; color: {t['text_selected']}; }}"
                f"QTableView {{ selection-background-color: {t['bg_selected']}; selection-color: {t['text_selected']}; }}"
            )
            def _on_theme_changed_history_table(name, tok, v=self.view):
                try:
                    v.setStyleSheet(
                        f"QTableView::item:hover {{ background: {tok['bg_row_hover']}; }}"
                        f"QTableView::item:selected {{ background: {tok['bg_selected']}; color: {tok['text_selected']}; }}"
                        f"QTableView {{ selection-background-color: {tok['bg_selected']}; selection-color: {tok['text_selected']}; }}"
                    )
                except RuntimeError:
                    # Widget was deleted, ignore
                    pass
            ThemeManager.instance().theme_changed.connect(_on_theme_changed_history_table)
            self.view.setMouseTracking(False)
            self.view.setFocusPolicy(Qt.NoFocus)
        except Exception:
            self.view.setStyleSheet(
                "QTableView::item:hover { background: transparent; }"
                "QTableView::item:selected { background: #0B63B8; color: white; }"
                "QTableView { selection-background-color: #0B63B8; selection-color: white; }"
            )
            self.view.setMouseTracking(False)
            self.view.setFocusPolicy(Qt.NoFocus)

        # Model
        self.model = QStandardItemModel(0, len(self.COLUMNS), self)
        headers = [title for _, title in self.COLUMNS]
        self.model.setHorizontalHeaderLabels(headers)

        self.view.setModel(self.model)

        # Header behaviour
        header = self.view.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setHighlightSections(False)

        layout.addWidget(self.view)

    def clear(self):
        self.model.removeRows(0, self.model.rowCount())

    def set_rows(self, rows):
        """Replace table contents with a list of dicts.

        Each dict can contain keys matching the first element of COLUMNS.
        Unknown/missing keys render as empty strings.
        """
        self.clear()
        for r in rows or []:
            self.add_row(r)

    def add_row(self, row: dict):
        items = []
        for key, _ in self.COLUMNS:
            val = row.get(key, "") if isinstance(row, dict) else ""
            # Format numeric values with two decimals when possible
            try:
                if isinstance(val, (int, float)):
                    cell = f"{val:.2f}"
                else:
                    cell = str(val)
            except Exception:
                cell = str(val)
            it = QStandardItem(cell)
            it.setEditable(False)
            items.append(it)
        self.model.appendRow(items)

    def get_selected(self):
        idx = self.view.selectionModel().currentIndex()
        if not idx.isValid():
            return None
        row = idx.row()
        data = {}
        for col, (key, _) in enumerate(self.COLUMNS):
            item = self.model.item(row, col)
            data[key] = item.text() if item is not None else ""
        return data