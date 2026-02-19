"""
Tab Bar Component - Custom tab bar with settings button
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


class TabBar(QWidget):
    """Custom tab bar with Favourites, All Symbols tabs and settings button"""
    
    tabChanged = Signal(int)  # 0 = Favourites, 1 = All Symbols
    settingsClicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Favourites tab
        self.favorites_tab = QPushButton("Favourites (7)")
        self.favorites_tab.setCheckable(True)
        self.favorites_tab.setChecked(True)  # Default selected
        self.favorites_tab.clicked.connect(lambda: self._on_tab_clicked(0))
        
        # Settings button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.settingsClicked.emit)
        
        # All Symbols tab
        self.all_symbols_tab = QPushButton("All Symbols (33)")
        self.all_symbols_tab.setCheckable(True)
        self.all_symbols_tab.clicked.connect(lambda: self._on_tab_clicked(1))
        
        layout.addWidget(self.favorites_tab)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.all_symbols_tab)
        layout.addStretch()
        
        self._apply_styles()
        self.current_tab = 0
    
    def _apply_styles(self):
        """Apply styling to tabs and settings button"""
        tab_style = """
            QPushButton {
                background: #f5f5f5;
                color: #666;
                border: none;
                border-bottom: 3px solid transparent;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
            QPushButton:checked {
                background: white;
                color: #1976d2;
                border-bottom: 3px solid #1976d2;
            }
        """
        
        settings_style = """
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
        """
        
        self.favorites_tab.setStyleSheet(tab_style)
        self.all_symbols_tab.setStyleSheet(tab_style)
        self.settings_btn.setStyleSheet(settings_style)
    
    def _on_tab_clicked(self, tab_index):
        """Handle tab click"""
        if tab_index == 0:
            self.favorites_tab.setChecked(True)
            self.all_symbols_tab.setChecked(False)
        else:
            self.favorites_tab.setChecked(False)
            self.all_symbols_tab.setChecked(True)
        
        if self.current_tab != tab_index:
            self.current_tab = tab_index
            self.tabChanged.emit(tab_index)
    
    def update_counts(self, favorites_count, all_count):
        """Update the count labels on tabs"""
        self.favorites_tab.setText(f"Favourites ({favorites_count})")
        self.all_symbols_tab.setText(f"All Symbols ({all_count})")
    
    def set_current_tab(self, index):
        """Programmatically set the current tab"""
        self._on_tab_clicked(index)
