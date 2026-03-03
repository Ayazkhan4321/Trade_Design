from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout, QWidget, QLabel
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor


class SymbolTreeView(QTreeWidget):
    """Tree view for displaying categorized symbols with favorite toggle"""

    favoriteToggled = Signal(str, bool)
    # Allow callers to disable hover-show behaviour (some hosts prefer no hover)
    show_hover_favorite = True

    def apply_theme(self):
        """Apply theme-aware styles to this tree view."""
        try:
            from Theme.theme_manager import ThemeManager
            t = ThemeManager.instance().tokens()
            bg     = t.get("bg_panel",      "#ffffff")
            sel    = t.get("bg_selected",   "#1565c0")
            sel_t  = t.get("text_selected", "#ffffff")
            hov    = t.get("bg_row_hover",  "#e3f2fd")
            txt    = t.get("text_primary",  "#1a202c")
            alt    = t.get("bg_row_alt",    "#f9fafb")
        except Exception:
            bg="#ffffff"; sel="#e6f2ff"; sel_t="#1a202c"; hov="#f7f7f7"; txt="#1a202c"; alt="#f9fafb"

        self.setStyleSheet(f"""
            QTreeWidget {{
                background: {bg};
                color: {txt};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                min-height: 34px;
                color: {txt};
            }}
            QTreeWidget::item:selected {{
                background: {sel};
                color: {sel_t};
            }}
            QTreeWidget::item:hover {{
                background: {hov};
            }}
            QTreeWidget::item:alternate {{
                background: {alt};
            }}
        """)

        # Re-colour existing category header rows and update name labels
        def _restyle(item):
            from PySide6.QtGui import QColor as _QC
            from PySide6.QtCore import Qt as _Qt
            data = item.data(0, _Qt.UserRole)
            if data and data.get("type") == "category":
                try:
                    from Theme.theme_manager import ThemeManager as _TM
                    _t2 = _TM.instance().tokens()
                    item.setBackground(0, _QC(_t2.get("bg_header", "#f0f4f8")))
                    item.setForeground(0, _QC(_t2.get("text_secondary", "#4a5568")))
                except Exception:
                    pass
            elif data and data.get("type") == "symbol":
                # Update the name label color inside the custom widget
                try:
                    from PySide6.QtWidgets import QTreeWidget as _TW
                    w = self.itemWidget(item, 0)
                    if w and hasattr(w, "name_label"):
                        w.name_label.setStyleSheet(
                            f"background: transparent; color: {txt}; "
                            "font-size: 11px; border: none;"
                        )
                except Exception:
                    pass
            for i in range(item.childCount()):
                _restyle(item.child(i))

        try:
            for i in range(self.topLevelItemCount()):
                _restyle(self.topLevelItem(i))
        except Exception:
            pass

    def update_symbols(self, symbols):
        """Update only the tree items for the given symbols (set of symbol names)"""
        if not symbols:
            return
        
        try:
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
                item = self.topLevelItem(i)
                if item:  # Safety check in case item was deleted
                    update_item_recursive(item)
        except RuntimeError:
            # Tree or items were deleted while updating, ignore
            pass
    
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
        self.apply_theme()

        # Subscribe to theme changes
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(
                lambda name, tokens: self.apply_theme()
            )
        except Exception:
            pass

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
            try:
                from Theme.theme_manager import ThemeManager
                _t = ThemeManager.instance().tokens()
                _cat_bg = _t.get("bg_header", "#f0f0f0")
                _cat_fg = _t.get("text_secondary", "#4a5568")
            except Exception:
                _cat_bg = "#f0f0f0"; _cat_fg = "#4a5568"
            category_item.setBackground(0, QColor(_cat_bg))
            category_item.setForeground(0, QColor(_cat_fg))
            
            # Set collapsed by default
            category_item.setExpanded(False)
            
            # Make category not selectable but clickable
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            
            # Add symbol items
            for symbol_data in category_symbols:
                symbol_name = symbol_data["symbol"]
                
                symbol_item = QTreeWidgetItem(category_item)
                
                # Create custom widget with symbol name label and star button
                widget = QWidget()
                widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(6, 0, 5, 0)
                layout.setSpacing(4)

                # Symbol name label — always visible
                try:
                    from Theme.theme_manager import ThemeManager as _TM
                    _tok = _TM.instance().tokens()
                    _sym_color = _tok.get("text_primary", "#1a202c")
                except Exception:
                    _sym_color = "#1a202c"

                name_label = QLabel(symbol_name)
                name_label.setStyleSheet(
                    f"background: transparent; color: {_sym_color}; "
                    "font-size: 11px; border: none;"
                )
                # Store label so apply_theme can recolor it
                widget.name_label = name_label

                # Store symbol data
                is_favorite = self.symbol_manager.is_favorite(symbol_name) if self.symbol_manager else False
                symbol_item.setData(0, Qt.UserRole, {
                    'type': 'symbol',
                    'name': symbol_name,
                    'is_favorite': is_favorite
                })

                # Create star button (initially hidden, shown on hover)
                star_btn = QPushButton("★" if is_favorite else "☆")
                star_btn.setFixedSize(20, 20)
                star_btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; border: none; "
                    f"color: {'#ffa500' if is_favorite else '#ccc'}; "
                    f"font-size: 14px; padding: 0px; }}"
                    f"QPushButton:hover {{ color: #ffa500; }}"
                )
                star_btn.clicked.connect(
                    lambda checked, name=symbol_name, item=symbol_item: self.toggle_favorite(name, item)
                )
                star_btn.hide()  # Initially hidden

                # Store star button reference in item
                symbol_item.setData(1, Qt.UserRole, star_btn)

                layout.addWidget(name_label)
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