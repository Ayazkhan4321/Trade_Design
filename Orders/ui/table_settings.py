"""
table_settings.py
=================
Table Settings dialogs for Order and History tabs.

Fix log
-------
* Use QCheckBox.toggled(bool) instead of stateChanged(int).
  In PySide6, stateChanged emits a plain int (2/0), and comparing it
  with Qt.Checked (a CheckState enum) always returns False → columns
  never hid. toggled() emits a real Python bool so the fix is clean.
* JSON files are stored next to this module (no ../.. path climbing).
* DEFAULT = False  →  all columns hidden until the user enables them,
  matching the unchecked UI the user sees.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFrame, QGridLayout, QLabel, QVBoxLayout,
)

LOG = logging.getLogger(__name__)

_HERE      = os.path.dirname(os.path.abspath(__file__))
_ORDER_CFG = os.path.join(_HERE, "orders_table_settings.json")
_HIST_CFG  = os.path.join(_HERE, "history_table_settings.json")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _svg_uri(size: int = 18) -> str:
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'"
        f" viewBox='0 0 {size} {size}'>"
        f"<rect rx='4' ry='4' width='{size}' height='{size}' fill='#2b7bd3'/>"
        f"<path d='M{int(size*.25)} {int(size*.50)}"
        f" L{int(size*.42)} {int(size*.67)}"
        f" L{int(size*.75)} {int(size*.30)}'"
        f" stroke='white' stroke-width='2' stroke-linecap='round'"
        f" stroke-linejoin='round' fill='none'/></svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _qss(name: str, sz: int) -> str:
    uri = _svg_uri(sz)
    return (
        f"QDialog#{name}{{background:white;border:2px solid #2b7bd3;border-radius:10px;}}"
        f"QDialog#{name} QLabel{{color:#2e3640;}}"
        f"QDialog#{name} QCheckBox::indicator{{width:{sz}px;height:{sz}px;}}"
        f"QDialog#{name} QCheckBox::indicator:unchecked"
        f"{{border:1.5px solid #b0b8c1;background:#fff;border-radius:4px;}}"
        f"QDialog#{name} QCheckBox::indicator:checked"
        f"{{image:url(\"{uri}\");border:1px solid #2b7bd3;border-radius:4px;}}"
        f"QDialog#{name} QCheckBox{{padding:6px 10px;border-radius:8px;background:transparent;}}"
    )


def _col_index(tv, name: str) -> Optional[int]:
    """Return column index matching *name* (case-insensitive, partial fallback)."""
    try:
        model = tv.model()
        n = name.strip().lower()
        count = model.columnCount()
        # exact match
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if h == n:
                return i
        # partial match
        for i in range(count):
            h = (model.headerData(i, Qt.Horizontal) or "").strip().lower()
            if n in h or h in n:
                return i
    except Exception as e:
        LOG.debug("_col_index(%r): %s", name, e)
    return None


def _set_visible(tv, header: str, visible: bool) -> None:
    """Show or hide a column by header name."""
    idx = _col_index(tv, header)
    if idx is None:
        LOG.warning("Column not found: %r", header)
        return
    tv.setColumnHidden(idx, not visible)
    LOG.debug("Column %r [%d] hidden=%s", header, idx, not visible)


def _load(path: str, labels: list[str], default: bool) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    changed = False
    for lbl in labels:
        if lbl not in data:
            data[lbl] = default
            changed = True
    if changed:
        _save(path, data)
    return data


def _save(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        LOG.exception("Cannot save %s", path)


# ─────────────────────────────────────────────────────────────────────────────
# OrderTableSettingsDialog
# ─────────────────────────────────────────────────────────────────────────────

class OrderTableSettingsDialog(QDialog):
    """
    Real-time column show/hide for the Orders table.

    COLUMNS = list of (checkbox_label, model_header_string)
    Model headers come from OrderModel.headers – adjust if yours differ.
    Use debug_print_headers(tv) to inspect the exact strings at runtime.
    """

    COLUMNS: list[tuple[str, str]] = [
        ("Entry Value",  "Entry Value"),
        ("Commission",   "Commission"),
        ("Market Value", "Market Value"),
        ("Swap",         "SWAP"),
        ("P/L in %",     "P/L IN %"),
        ("Remarks",      "Remarks"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.setObjectName("OrderTableSettingsDialog")
        self.setWindowTitle("Table Settings")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setStyleSheet(_qss("OrderTableSettingsDialog", 18))

        self._tv  = table_view          # direct reference – most reliable
        self._cfg = _load(
            _ORDER_CFG,
            [lbl for lbl, _ in self.COLUMNS] + ["Multi-Target SL/TP"],
            default=False,              # unchecked / hidden by default
        )

        self._build()
        self._apply_all()              # sync table to stored state on open

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(4)

        t = QLabel("Table Settings")
        t.setStyleSheet("font-size:18px;font-weight:700;")
        lay.addWidget(t)

        s = QLabel("Customize your table display")
        s.setStyleSheet("color:gray;font-size:12px;")
        lay.addWidget(s)

        lv = QLabel("VISIBLE OPTIONS")
        lv.setStyleSheet("font-weight:700;color:#6e7480;margin-top:10px;font-size:11px;")
        lay.addWidget(lv)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(2)

        for i, (label, header) in enumerate(self.COLUMNS):
            cb = self._make_cb(label, header)
            grid.addWidget(cb, i // 2, i % 2)
        lay.addLayout(grid)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#e6e9ec;margin-top:10px;margin-bottom:4px;")
        lay.addWidget(sep)

        lm = QLabel("\U0001F3C6  MASTER FEATURES")
        lm.setStyleSheet("font-weight:700;color:#6e7480;font-size:11px;")
        lay.addWidget(lm)

        cb_m = QCheckBox("Multi-Target SL/TP")
        cb_m.setChecked(bool(self._cfg.get("Multi-Target SL/TP", False)))
        cb_m.setCursor(Qt.PointingHandCursor)
        # feature-only toggle (no column to hide)
        cb_m.toggled.connect(
            lambda checked: self._persist_only("Multi-Target SL/TP", checked)
        )
        lay.addWidget(cb_m)

    def _make_cb(self, label: str, header: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.blockSignals(True)
        cb.setChecked(bool(self._cfg.get(label, False)))
        cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        # ↓ toggled(bool) – the CORRECT signal in PySide6 for true/false toggle
        #   stateChanged(int) comparison with Qt.Checked enum was always False!
        cb.toggled.connect(
            lambda checked, lbl=label, hdr=header: self._on_toggle(lbl, hdr, checked)
        )
        return cb

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_toggle(self, label: str, header: str, checked: bool) -> None:
        """Called immediately when user ticks/unticks. checked is a real bool."""
        # 1. Persist
        self._cfg[label] = checked
        _save(_ORDER_CFG, self._cfg)

        # 2. Apply to table
        tv = self._get_tv()
        if tv is None:
            LOG.warning("_on_toggle(%r): table_view is None", label)
            return
        _set_visible(tv, header, checked)

    def _persist_only(self, key: str, checked: bool) -> None:
        self._cfg[key] = checked
        _save(_ORDER_CFG, self._cfg)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_tv(self):
        if self._tv is not None:
            return self._tv
        # fallback: walk parent chain
        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "orders_tab", "table", "table_view"),
                ("table", "table_view"),
            ):
                try:
                    obj = p
                    for attr in path:
                        obj = getattr(obj, attr)
                    if obj is not None:
                        self._tv = obj
                        return obj
                except AttributeError:
                    pass
            try:
                p = p.parent()
            except Exception:
                break
        return None

    def _apply_all(self):
        """Sync every column's visibility to match the stored config."""
        tv = self._get_tv()
        if tv is None:
            LOG.debug("_apply_all: table_view not available")
            return
        for label, header in self.COLUMNS:
            _set_visible(tv, header, bool(self._cfg.get(label, False)))


# ─────────────────────────────────────────────────────────────────────────────
# HistoryTableSettingsDialog
# ─────────────────────────────────────────────────────────────────────────────

class HistoryTableSettingsDialog(QDialog):
    """Real-time column show/hide for the History table."""

    COLUMNS: list[tuple[str, str]] = [
        ("Entry Value",  "Entry Value"),
        ("Commission",   "Commission"),
        ("Closed Value", "Closed Value"),
        ("Swap",         "SWAP"),
        ("P/L in %",     "P/L IN %"),
        ("Remark",       "Remark"),
    ]

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.setObjectName("HistoryTableSettingsDialog")
        self.setWindowTitle("Table Settings")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet(_qss("HistoryTableSettingsDialog", 16))

        self._tv  = table_view
        self._cfg = _load(
            _HIST_CFG,
            [lbl for lbl, _ in self.COLUMNS],
            default=False,
        )

        self._build()
        self._apply_all()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(4)

        t = QLabel("Table Settings")
        t.setStyleSheet("font-size:16px;font-weight:700;")
        lay.addWidget(t)

        s = QLabel("Customize display")
        s.setStyleSheet("color:gray;font-size:12px;")
        lay.addWidget(s)

        lv = QLabel("VISIBLE OPTIONS")
        lv.setStyleSheet("font-weight:700;color:#6e7480;margin-top:8px;font-size:11px;")
        lay.addWidget(lv)

        grid = QGridLayout()
        for i, (label, header) in enumerate(self.COLUMNS):
            cb = self._make_cb(label, header)
            grid.addWidget(cb, i // 2, i % 2)
        lay.addLayout(grid)

    def _make_cb(self, label: str, header: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.blockSignals(True)
        cb.setChecked(bool(self._cfg.get(label, False)))
        cb.blockSignals(False)
        cb.setCursor(Qt.PointingHandCursor)
        cb.toggled.connect(
            lambda checked, lbl=label, hdr=header: self._on_toggle(lbl, hdr, checked)
        )
        return cb

    def _on_toggle(self, label: str, header: str, checked: bool) -> None:
        self._cfg[label] = checked
        _save(_HIST_CFG, self._cfg)
        tv = self._get_tv()
        if tv is None:
            LOG.warning("_on_toggle(%r): history table_view is None", label)
            return
        _set_visible(tv, header, checked)

    def _get_tv(self):
        if self._tv is not None:
            return self._tv
        p = self.parent()
        while p is not None:
            for path in (
                ("orders_widget", "history_tab", "view"),
                ("orders_widget", "history_tab", "table_view"),
                ("table", "table_view"),
            ):
                try:
                    obj = p
                    for attr in path:
                        obj = getattr(obj, attr)
                    if obj is not None:
                        self._tv = obj
                        return obj
                except AttributeError:
                    pass
            try:
                p = p.parent()
            except Exception:
                break
        return None

    def _apply_all(self):
        tv = self._get_tv()
        if tv is None:
            return
        for label, header in self.COLUMNS:
            _set_visible(tv, header, bool(self._cfg.get(label, False)))


# ─────────────────────────────────────────────────────────────────────────────
# Debug helper
# ─────────────────────────────────────────────────────────────────────────────

def debug_print_headers(table_view) -> None:
    """Print all column indices + header strings. Call once to verify names."""
    try:
        model = table_view.model()
        count = model.columnCount()
        print(f"\n{'='*52}\nTABLE HEADERS ({count} columns)\n{'='*52}")
        for i in range(count):
            h = model.headerData(i, Qt.Horizontal)
            print(f"  [{i:2d}]  {repr(h):35s}  hidden={table_view.isColumnHidden(i)}")
        print("=" * 52)
    except Exception as exc:
        print(f"debug_print_headers error: {exc}")