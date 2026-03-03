from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from Orders.ui.main_window import OrdersWidget
from Orders.ui.table_settings import HistoryTableSettingsDialog

app = QApplication.instance() or QApplication([])
orders = OrdersWidget()
parent = QWidget()
parent.orders_widget = orders
# instantiate just like the tests (no table_view argument)
hist_dlg = HistoryTableSettingsDialog(parent)
print('initial table_view attr', hist_dlg.table_view)
# prepare settings path
import tempfile, json
hist_dlg._hist_settings_path = tempfile.gettempdir() + '/hist.json'
hdrs = [orders.history_tab.view.model().headerData(i, Qt.Horizontal) for i in range(orders.history_tab.view.model().columnCount())]
print('headers', hdrs)
opt = list(hist_dlg._checkboxes.keys())[0]
# find case-insensitive index
idx = next(i for i,h in enumerate(hdrs) if h.lower() == opt.lower())
print('testing opt', opt, 'idx', idx)


# replicate internals of _on_history_state_changed for debugging
key = opt
state = Qt.Unchecked
# persist
try:
    with open(hist_dlg._hist_settings_path, 'r', encoding='utf-8') as f:
        hist = json.load(f)
except Exception:
    hist = {}
hist[key] = bool(state == Qt.Checked)
with open(hist_dlg._hist_settings_path, 'w', encoding='utf-8') as f:
    json.dump(hist, f, indent=2)

# attempt hide, identical to method
try:
    table_view = getattr(hist_dlg, 'table_view', None)
    headers2 = None
    if table_view is not None:
        try:
            headers2 = table_view.model().headers
        except Exception:
            headers2 = None
    if table_view is None or headers2 is None:
        parent = hist_dlg.parent()
        if parent is not None:
            try:
                table_view = parent.orders_widget.history_tab.view
                headers2 = [
                    table_view.model().headerData(i, Qt.Horizontal)
                    for i in range(table_view.model().columnCount())
                ]
            except Exception:
                try:
                    table_view = parent.table.table_view
                    headers2 = parent.table.model.headers
                except Exception:
                    pass
    print('calculated table_view', table_view)
    print('calculated headers2', headers2)
    if headers2:
        try:
            idx2 = next(i for i,h in enumerate(headers2) if h.lower() == key.lower())
            canonical = headers2[idx2]
        except Exception as e:
            print('header lookup failed', e)
            canonical = key
            idx2 = None
    else:
        canonical = key
        idx2 = None
    print('idx2', idx2, 'canonical', canonical)
    if canonical != key:
        try:
            hist.pop(key, None)
            hist[canonical] = bool(state == Qt.Checked)
            with open(hist_dlg._hist_settings_path, 'w', encoding='utf-8') as f:
                json.dump(hist, f, indent=2)
        except Exception:
            pass
    if table_view is not None and idx2 is not None and headers2:
        table_view.setColumnHidden(idx2, not hist.get(canonical, False))
        print('setColumnHidden called with', idx2, not hist.get(canonical, False))
except Exception as e:
    print('error in hide logic', e)

print('column hidden after simulated toggle', orders.history_tab.view.isColumnHidden(idx))
print('hist file contents:')
print(json.load(open(hist_dlg._hist_settings_path)))

