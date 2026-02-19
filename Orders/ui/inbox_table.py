from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QPushButton, QHBoxLayout
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QSize, Signal


class InboxTable(QWidget):
    """Inbox table for messages related to orders.

    Columns: Subject, From, Time, Actions (Actions left empty for now).
    Provides `set_rows(list[dict])` to populate later from API.
    """

    COLUMNS = [
        ("subject", "Subject"),
        ("from", "From"),
        ("time", "Time"),
        ("actions", "Actions"),
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

        # Disable hover background and set selection style
        try:
            self.view.setStyleSheet(
                "QTableView::item:hover { background: transparent; }"
                "QTableView::item:selected { background: #0B63B8; color: white; }"
            )
            self.view.setMouseTracking(False)
            self.view.setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass

        # Model
        self.model = QStandardItemModel(0, len(self.COLUMNS), self)
        headers = [title for _, title in self.COLUMNS]
        self.model.setHorizontalHeaderLabels(headers)

        self.view.setModel(self.model)

        # Header behaviour: make Subject broader and Actions column fixed
        header = self.view.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Subject
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # From
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Time
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Actions
        header.setHighlightSections(False)
        # Set a reasonable width for actions column (eye button)
        try:
            self.view.setColumnWidth(3, 48)
        except Exception:
            pass

        layout.addWidget(self.view)

    def clear(self):
        self.model.removeRows(0, self.model.rowCount())

    def set_rows(self, rows):
        """Populate the inbox table from a list of dicts.

        Expected keys: 'subject', 'from', 'time', 'actions' (actions optional).
        """
        self.clear()
        for r in rows or []:
            self.add_row(r)

    def add_row(self, row: dict):
        items = []
        # Subject, From, Time
        for key, _ in self.COLUMNS[:3]:
            val = row.get(key, "") if isinstance(row, dict) else ""
            try:
                cell = str(val)
            except Exception:
                cell = ""
            it = QStandardItem(cell)
            it.setEditable(False)
            items.append(it)

        # Append a placeholder item for the actions column to keep row indexing stable
        action_placeholder = QStandardItem("")
        action_placeholder.setEditable(False)
        items.append(action_placeholder)
        self.model.appendRow(items)

        # Add a clickable eye button in the Actions column using setIndexWidget
        try:
            row_index = self.model.rowCount() - 1
            idx = self.model.index(row_index, 3)
            btn = QPushButton("👁")
            btn.setFlat(True)
            btn.setFixedSize(QSize(36, 24))
            btn.setCursor(Qt.PointingHandCursor)
            # Store original payload on the button for handler reference
            try:
                btn._payload = row
            except Exception:
                btn._payload = {}

            def _on_click(payload=btn._payload):
                # Minimal handler: log and emit selection - real handler can open message viewer
                try:
                    print("[Inbox] View message:", payload)
                except Exception:
                    pass

            btn.clicked.connect(_on_click)
            # Use a small container widget to center the button
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(6, 0, 6, 0)
            h.addWidget(btn)
            h.addStretch()
            self.view.setIndexWidget(idx, container)
        except Exception:
            pass

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
