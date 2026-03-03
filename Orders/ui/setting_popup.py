from PySide6.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QPushButton, QDialog

class TableSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Table Settings")
        self.setFixedSize(250, 250)  # Adjust as needed

        layout = QVBoxLayout()

        # Add checkboxes for each column
        self.entry_value_cb = QCheckBox("Entry Value")
        self.market_value_cb = QCheckBox("Market Value")
        self.pl_percent_cb = QCheckBox("P/L in %")
        self.multi_target_cb = QCheckBox("Multi-Target SL/TP")
        self.commission_cb = QCheckBox("Commission")
        self.swap_cb = QCheckBox("Swap")
        self.remark_cb = QCheckBox("Remark")

        # Check all by default and add to layout
        for cb in [self.entry_value_cb, self.market_value_cb, self.pl_percent_cb,
                   self.multi_target_cb, self.commission_cb, self.swap_cb, self.remark_cb]:
            cb.setChecked(True)
            layout.addWidget(cb)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)


# Example usage inside your Orders tab widget
def open_table_settings(self):
    dlg = TableSettingsDialog(self)
    if dlg.exec():  # Note: exec() instead of exec_()
        # Read checkbox values to show/hide columns
        print("Entry Value:", dlg.entry_value_cb.isChecked())
        print("Market Value:", dlg.market_value_cb.isChecked())
        print("P/L in %:", dlg.pl_percent_cb.isChecked())
        print("Multi-Target SL/TP:", dlg.multi_target_cb.isChecked())
        print("Commission:", dlg.commission_cb.isChecked())
        print("Swap:", dlg.swap_cb.isChecked())
        print("Remark:", dlg.remark_cb.isChecked())
    