from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout, QWidget
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor


class SymbolTreeView(QTreeWidget):
    """Tree view for displaying categorized symbols with favorite toggle"""

    favoriteToggled = Signal(str, bool)
    # Allow callers to disable hover-show behaviour (some hosts prefer no hover)
    show_hover_favorite = True

    def update_symbols(self, symbols):
        """Update only the tree items for the given symbols (set of symbol names)"""
        if not symbols:
            return
        def update_item_recursive(item):
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get('type') == 'symbol':
                symbol_name = item_data.get('name')
                if symbol_name in symbols:
                    # Optionally update favorite status or other visuals
                    is_favorite = self.symbol_manager.is_favorite(symbol_name) if self.symbol_manager else False
                    item_data['is_favorite'] = is_favorite
                    # Update star button if present
                    star_btn = item.data(1, Qt.UserRole)
                    if star_btn:
                        star_btn.setText("★" if is_favorite else "☆")
                        star_btn.setStyleSheet(f"""
                            QPushButton {{
                                background: transparent;
                                border: none;
                                color: {'#ffa500' if is_favorite else '#ccc'};
                                font-size: 16px;
                                padding: 0px;
                            }}
                            QPushButton:hover {{
                                color: #ffa500;
                            }}
                        """)
            for i in range(item.childCount()):
                update_item_recursive(item.child(i))
        # Traverse all top-level items
        for i in range(self.topLevelItemCount()):
            update_item_recursive(self.topLevelItem(i))
    
    def __init__(self, symbol_manager, account_id=None, active_account_id=None, parent=None):
        super().__init__(parent)
        self.symbol_manager = symbol_manager
        self.account_id = account_id
        self.active_account_id = active_account_id

        # --- QTreeWidget Styling ---
        # Enable mouse tracking so itemEntered signals fire for hover
        self.setMouseTracking(True)
        try:
            self.viewport().setMouseTracking(True)
        except Exception:
            pass

        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(12)
        from PySide6.QtWidgets import QAbstractItemView
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Prevent inline editing when clicking a symbol; we open panels instead
        try:
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        except Exception:
            pass
        self.setFont(QFont("Segoe UI", 10))
        self.setColumnCount(1)
        # Light hover background, avoid dark system-blue on hover
        # Increase minimum item height slightly for readability
        self.setStyleSheet(
            "QTreeWidget { background: #fff; border: none; }"
            "QTreeWidget::item { min-height: 34px; }"
            "QTreeWidget::item:selected { background: #e6f2ff; }"
            "QTreeWidget::item:hover { background: #f7f7f7; }"
        )

        # Track hovered item for showing star button
        self.hovered_item = None
        self.itemEntered.connect(self.on_item_hovered)

        # Connect item clicked to handle category expansion
        self.itemClicked.connect(self.on_item_clicked)
        
    def set_symbols(self, symbols):
        """Populate tree with categorized symbols"""
        # Clear hovered item reference before clearing tree
        self.hovered_item = None
        
        self.clear()
        
        # Categorize symbols
        categories = self._categorize_symbols(symbols)
        
        # Add categories and symbols
        for category_name, category_symbols in categories.items():
            if not category_symbols:
                continue
                
            # Create category item
            category_item = QTreeWidgetItem(self)
            category_item.setText(0, f"▸ {category_name} ({len(category_symbols)})")
            category_item.setData(0, Qt.UserRole, {'type': 'category', 'name': category_name})
            
            # Style category
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            category_item.setFont(0, font)
            category_item.setBackground(0, QColor("#f0f0f0"))
            
            # Set collapsed by default
            category_item.setExpanded(False)
            
            # Make category not selectable but clickable
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            
            # Add symbol items
            for symbol_data in category_symbols:
                symbol_name = symbol_data["symbol"]
                
                symbol_item = QTreeWidgetItem(category_item)
                
                # Create custom widget with symbol name and star button
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 0, 5, 0)
                layout.setSpacing(5)
                
                # Symbol name label (as text in tree item)
                symbol_item.setText(0, f"  {symbol_name}")
                
                # Store symbol data
                is_favorite = self.symbol_manager.is_favorite(symbol_name) if self.symbol_manager else False
                symbol_item.setData(0, Qt.UserRole, {
                    'type': 'symbol',
                    'name': symbol_name,
                    'is_favorite': is_favorite
                })
                
                # Create star button (initially hidden)
                star_btn = QPushButton("★" if is_favorite else "☆")
                star_btn.setFixedSize(20, 20)
                star_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        color: {'#ffa500' if is_favorite else '#ccc'};
                        font-size: 16px;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        color: #ffa500;
                    }}
                """)
                star_btn.clicked.connect(lambda checked, name=symbol_name, item=symbol_item: self.toggle_favorite(name, item))
                star_btn.hide()  # Initially hidden
                
                # Store star button reference in item
                symbol_item.setData(1, Qt.UserRole, star_btn)
                
                layout.addStretch()
                layout.addWidget(star_btn)
                
                self.setItemWidget(symbol_item, 0, widget)
    
    def _categorize_symbols(self, symbols):
        """Group symbols into categories"""
        categories = {
            'Majors': [],
            'Minors': [],
            'Metals': [],
            'ENERGY': [],
            'CRYPTO': []
        }
        
        for symbol in symbols:
            symbol_name = symbol["symbol"]
            
            # Categorization logic
            if any(major in symbol_name for major in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']):
                categories['Majors'].append(symbol)
            elif any(metal in symbol_name for metal in ['XAU', 'XAG', 'GOLD', 'SILVER']):
                categories['Metals'].append(symbol)
            elif any(energy in symbol_name for energy in ['OIL', 'WTI', 'BRENT', 'USOIL', 'UKOIL']):
                categories['ENERGY'].append(symbol)
            elif any(crypto in symbol_name for crypto in ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM']):
                categories['CRYPTO'].append(symbol)
            elif any(curr in symbol_name for curr in ['EUR', 'GBP', 'USD', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']):
                categories['Minors'].append(symbol)
            else:
                categories['Minors'].append(symbol)
        
        return categories
    
    def on_item_clicked(self, item, column):
        """Handle item clicks - expand/collapse categories"""
        item_data = item.data(0, Qt.UserRole)
        
        if item_data and item_data.get('type') == 'category':
            # Toggle expansion of category
            is_expanded = item.isExpanded()
            item.setExpanded(not is_expanded)
            
            # Update arrow indicator
            category_name = item_data['name']
            child_count = item.childCount()
            arrow = "▾" if not is_expanded else "▸"
            item.setText(0, f"{arrow} {category_name} ({child_count})")
    
    def on_item_hovered(self, item, column):
        """Show/hide star button on hover"""
        if not getattr(self, 'show_hover_favorite', True):
            return
        # Hide previous star button with safety check
        if self.hovered_item is not None:
            try:
                # Check if item is still valid
                prev_data = self.hovered_item.data(0, Qt.UserRole)
                if prev_data and prev_data.get('type') == 'symbol':
                    star_btn = self.hovered_item.data(1, Qt.UserRole)
                    if star_btn:
                        star_btn.hide()
            except RuntimeError:
                # Item was deleted, ignore
                pass
            finally:
                self.hovered_item = None
        
        # Show current star button
        try:
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get('type') == 'symbol':
                star_btn = item.data(1, Qt.UserRole)
                if star_btn:
                    star_btn.show()
                self.hovered_item = item
        except RuntimeError:
            # Item was deleted during processing
            pass
    
    def leaveEvent(self, event):
        """Hide star button when mouse leaves"""
        if self.hovered_item is not None:
            try:
                item_data = self.hovered_item.data(0, Qt.UserRole)
                if item_data and item_data.get('type') == 'symbol':
                    star_btn = self.hovered_item.data(1, Qt.UserRole)
                    if star_btn:
                        star_btn.hide()
            except RuntimeError:
                # Item was deleted, ignore
                pass
            finally:
                self.hovered_item = None
        super().leaveEvent(event)
    
    def toggle_favorite(self, symbol_name, item):
        """Toggle favorite status"""
        if not self.symbol_manager:
            return
        
        # Toggle in manager
        self.symbol_manager.toggle_favorite(symbol_name)
        is_favorite = self.symbol_manager.is_favorite(symbol_name)
        
        # Update item data
        try:
            item_data = item.data(0, Qt.UserRole)
            item_data['is_favorite'] = is_favorite
            item.setData(0, Qt.UserRole, item_data)
            
            # Update star button
            star_btn = item.data(1, Qt.UserRole)
            if star_btn:
                star_btn.setText("★" if is_favorite else "☆")
                star_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        color: {'#ffa500' if is_favorite else '#ccc'};
                        font-size: 16px;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        color: #ffa500;
                    }}
                """)
        except RuntimeError:
            # Item was deleted during processing
            pass
        
        # Clear hovered item reference
        self.hovered_item = None
        
        # Emit signal
        self.favoriteToggled.emit(symbol_name, is_favorite)
    
    def close_expanded_panel(self):
        """Compatibility method - no panels in tree view"""
        pass
    
    def set_advance_view(self, enabled):
        """Compatibility method - tree view doesn't use this"""
        pass
