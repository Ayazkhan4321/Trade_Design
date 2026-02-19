from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QCheckBox, QPushButton, QFrame
)
from PySide6.QtCore import Qt
import base64
import os
import json


class OrderTableSettingsDialog(QDialog):
    """Larger dialog (image1) for the live Orders tab.

    Scoped by object name so app-wide styles are not affected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OrderTableSettingsDialog")
        self.setWindowTitle("Tabel Settings")
        self.setModal(True)
        self.setMinimumWidth(480)

        # blue rounded-check SVG
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 18 18'>"
            "<rect rx='4' ry='4' width='18' height='18' fill='#2b7bd3'/>"
            "<path d='M4.5 9.0 L7.5 12.0 L13.0 6.0' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
            "</svg>"
        )
        svg_b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        data_uri = f"data:image/svg+xml;base64,{svg_b64}"

        # Scoped stylesheet (only affects this dialog)
        self.setStyleSheet(
            "QDialog#OrderTableSettingsDialog { background: white; border: 2px solid #2b7bd3; border-radius:10px; }\n"
            "QDialog#OrderTableSettingsDialog QLabel { color: #2e3640; }\n"
            "QDialog#OrderTableSettingsDialog QCheckBox::indicator { width:18px; height:18px; }\n"
            "QDialog#OrderTableSettingsDialog QCheckBox::indicator:unchecked { border:1px solid #d0d6dc; background:transparent; border-radius:4px; }\n"
            "QDialog#OrderTableSettingsDialog QCheckBox::indicator:checked { image: url(\"" + data_uri + "\"); background-color:#2b7bd3; border:1px solid #2b7bd3; border-radius:4px; }\n"
            "QDialog#OrderTableSettingsDialog QCheckBox { padding:8px; border-radius:10px; background:transparent; }\n"
            "QDialog#OrderTableSettingsDialog QCheckBox:checked { background: transparent; color: #222; }\n"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("Tabel Settings")
        title.setStyleSheet("font-size:18px; font-weight:700;")
        layout.addWidget(title)

        subtitle = QLabel("Customize your table display")
        subtitle.setStyleSheet("color:gray;")
        layout.addWidget(subtitle)

        vis_label = QLabel("VISIBLE OPTIONS")
        vis_label.setStyleSheet("font-weight:700; color:#6e7480; margin-top:8px;")
        layout.addWidget(vis_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        options = [
            "Entry Value",
            "Commission",
            "Market Value",
            "Swap",
            "P/L in %",
            "Remark",
        ]

        # persistence path (store per-workspace under project root)
        proj_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self._settings_path = os.path.join(proj_root, 'orders_table_settings.json')
        try:
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
        except Exception:
            self._settings = {}

        # Ensure all options default to True when not present
        defaults_added = False
        for opt in options + ['Multi-Target SL/TP']:
            if opt not in self._settings:
                self._settings[opt] = True
                defaults_added = True
        if defaults_added:
            try:
                with open(self._settings_path, 'w', encoding='utf-8') as f:
                    json.dump(self._settings, f, indent=2)
            except Exception:
                pass

        self._checkboxes = {}
        for i, opt in enumerate(options):
            cb = QCheckBox(opt)
            default = True
            val = self._settings.get(opt, default)
            cb.setChecked(bool(val))
            cb.setCursor(Qt.PointingHandCursor)
            cb.stateChanged.connect(lambda st, key=opt: self._on_state_changed(key, st))
            self._checkboxes[opt] = cb
            r = i // 2
            c = i % 2
            grid.addWidget(cb, r, c)

        layout.addLayout(grid)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#e6e9ec; margin-top:10px; margin-bottom:10px;")
        layout.addWidget(line)

        crown_lbl = QLabel("\uD83C\uDFC6  MASTER FEATURES")
        crown_lbl.setStyleSheet("font-weight:700; color:#6e7480;")
        layout.addWidget(crown_lbl)

        mcb = QCheckBox("Multi-Target SL/TP")
        mcb.setChecked(bool(self._settings.get('Multi-Target SL/TP', True)))
        mcb.setCursor(Qt.PointingHandCursor)
        mcb.stateChanged.connect(lambda st, key='Multi-Target SL/TP': self._on_state_changed(key, st))
        layout.addWidget(mcb)

    def _on_state_changed(self, key, state):
        try:
            self._settings[key] = bool(state == Qt.Checked)
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass


class HistoryTableSettingsDialog(QDialog):
    """Compact dialog (image2) for History tab.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HistoryTableSettingsDialog")
        self.setWindowTitle("Tabel Settings")
        self.setModal(True)
        self.setMinimumWidth(360)

        # SVG checkmark for history dialog (smaller)
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'>"
            "<rect rx='4' ry='4' width='16' height='16' fill='#2b7bd3'/>"
            "<path d='M4 8 L6.5 11 L12 5' stroke='white' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' fill='none'/>"
            "</svg>"
        )
        svg_b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        data_uri = f"data:image/svg+xml;base64,{svg_b64}"

        self.setStyleSheet(
            "QDialog#HistoryTableSettingsDialog { background: white; border: 2px solid #2b7bd3; border-radius:12px; }\n"
            "QDialog#HistoryTableSettingsDialog QCheckBox::indicator { width:16px; height:16px; }\n"
            "QDialog#HistoryTableSettingsDialog QCheckBox::indicator:unchecked { border:1px solid #d0d6dc; background:transparent; border-radius:4px; }\n"
            "QDialog#HistoryTableSettingsDialog QCheckBox::indicator:checked { image: url(\"" + data_uri + "\"); background-color:#2b7bd3; border:1px solid #2b7bd3; border-radius:4px; }\n"
            "QDialog#HistoryTableSettingsDialog QCheckBox { padding:8px; border-radius:10px; background:transparent; }\n"
            "QDialog#HistoryTableSettingsDialog QCheckBox:checked { background: transparent; color: #222; }\n"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        title = QLabel("Tabel Settings")
        title.setStyleSheet("font-size:16px; font-weight:700;")
        layout.addWidget(title)

        subtitle = QLabel("Customize display")
        subtitle.setStyleSheet("color:gray;")
        layout.addWidget(subtitle)

        vis_label = QLabel("VISIBLE OPTIONS")
        vis_label.setStyleSheet("font-weight:700; color:#6e7480; margin-top:8px;")
        layout.addWidget(vis_label)

        grid = QGridLayout()
        options = [
            "Entry Value",
            "Commission",
            "Closed Value",
            "Swap",
            "P/L in %",
            "Remarks",
        ]
        # history settings persistence
        proj_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self._hist_settings_path = os.path.join(proj_root, 'history_table_settings.json')
        try:
            with open(self._hist_settings_path, 'r', encoding='utf-8') as f:
                hist_settings = json.load(f)
        except Exception:
            hist_settings = {}

        # Ensure history options default to True
        hist_defaults_added = False
        for opt in options:
            if opt not in hist_settings:
                hist_settings[opt] = True
                hist_defaults_added = True
        if hist_defaults_added:
            try:
                with open(self._hist_settings_path, 'w', encoding='utf-8') as f:
                    json.dump(hist_settings, f, indent=2)
            except Exception:
                pass

        for i, opt in enumerate(options):
            cb = QCheckBox(opt)
            cb.setChecked(bool(hist_settings.get(opt, True)))
            cb.setCursor(Qt.PointingHandCursor)
            cb.stateChanged.connect(lambda st, key=opt: self._on_history_state_changed(key, st))
            r = i // 2
            c = i % 2
            grid.addWidget(cb, r, c)

        layout.addLayout(grid)

    def _on_history_state_changed(self, key, state):
        try:
            try:
                with open(self._hist_settings_path, 'r', encoding='utf-8') as f:
                    hist = json.load(f)
            except Exception:
                hist = {}
            hist[key] = bool(state == Qt.Checked)
            with open(self._hist_settings_path, 'w', encoding='utf-8') as f:
                json.dump(hist, f, indent=2)
        except Exception:
            pass

        
