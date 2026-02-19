# Quick Start Guide - MarketWatch Trading App

## ✅ What's New

### 1. **Tabbed Interface**
- **Favourites Tab**: Shows your 7 favorite symbols with ★ indicator
- **All Symbols Tab**: Shows all 33 available symbols
- **Settings Button (⚙)**: Located between tabs for quick access

### 2. **Organized Code Structure**

```
Production-Level Folders:
├── core/           → Business logic (SymbolManager)
├── models/         → Data models (MarketModel)
├── ui/             → Main UI (MarketWidget, MarketTable, TradePanel)
├── components/     → Reusable components (TabBar)
└── widgets/        → Custom widgets (LotPresetWidget)
```

### 3. **How to Use**

#### **Switch Between Tabs**
- Click "Favourites (7)" to see favorite symbols
- Click "All Symbols (33)" to see all available symbols
- Numbers update automatically when you add/remove favorites

#### **Add/Remove Favorites**
1. Click on any symbol row to open the trade panel
2. Click the ★/☆ button at the top
3. Yellow ★ = Favorite, Gray ☆ = Not favorite
4. Changes reflect immediately in both tabs

#### **Search Symbols**
1. Type in the search box
2. Results filter in real-time
3. Search works within the active tab:
   - Favourites tab: searches only favorites
   - All Symbols tab: searches all symbols

#### **Trade Panel Features**
- **Buy/Sell Buttons**: Large buttons with current prices
- **Lot Controls**: 
  - Select preset (0.01, 0.10, 1.00)
  - Click + to add selected value
  - Click - to decrease by 0.01
  - Manual input supported
- **Quick Actions**:
  - ★ = Toggle favorite
  - + = Place order (ready for your dialog)
  - ⓘ = Info
  - ✕ = Close panel

### 4. **Code Organization Benefits**

#### **Easy to Maintain**
Each feature is in its own file:
- Need to change favorites logic? → `core/symbol_manager.py`
- Need to update table display? → `ui/market_table.py`
- Need to modify tabs? → `components/tab_bar.py`

#### **Easy to Extend**
Add new features without breaking existing code:
- New widget? → Add to `widgets/`
- New data source? → Add to `core/`
- New component? → Add to `components/`

#### **Production Ready**
- Clear separation of concerns
- Modular components
- Signal-based communication
- Documented code
- Scalable architecture

### 5. **Key Files Explained**

| File | Purpose | When to Edit |
|------|---------|--------------|
| `core/symbol_manager.py` | Manages all symbols & favorites | Add symbols, change default favorites |
| `components/tab_bar.py` | Custom tab widget | Modify tab appearance or behavior |
| `ui/market_widget.py` | Main container | Change overall layout |
| `ui/market_table.py` | Symbol table | Modify table behavior |
| `ui/trade_panel.py` | Trade interface | Update trading controls |
| `widgets/lot_preset_widget.py` | Lot buttons | Change lot presets |

### 6. **Adding New Symbols**

Edit `core/symbol_manager.py` (line ~16):

```python
self._all_symbols = [
    ("EURUSD", "1.17347", "1.17361"),
    ("NEWPAIR", "123.45", "123.67"),  # ← Add here
    ...
]
```

Set default favorites (line ~30):

```python
self._favorites = set([
    "EURUSD", "GBPUSD", "NEWPAIR"  # ← Add here
])
```

### 7. **Settings Button**

Currently shows a message dialog. To implement:

Edit `ui/market_widget.py` → `_on_settings_clicked()` method

```python
def _on_settings_clicked(self):
    # Replace with your settings dialog
    settings_dialog = SettingsDialog(self)
    settings_dialog.exec()
```

### 8. **Place Order Button**

Ready for your implementation in `ui/trade_panel.py` → `place_order()` method:

```python
def place_order(self):
    # Replace with your order dialog
    order_dialog = OrderDialog(self.symbol, self.current_lot)
    order_dialog.exec()
```

## 🎯 Testing Checklist

- ✅ Switch between Favourites and All Symbols tabs
- ✅ Search symbols in both tabs
- ✅ Toggle favorites with ★ button
- ✅ Verify tab counts update automatically
- ✅ Click settings button (⚙)
- ✅ Open/close trade panels
- ✅ Adjust lot sizes with +/- buttons
- ✅ Test lot presets (0.01, 0.10, 1.00)
- ✅ Click place order button (+)

## 📁 File Structure Overview

```
MarketWatch_jetfyx/
│
├── 📂 core/                    ← Business Logic
│   ├── __init__.py
│   └── symbol_manager.py       ← Symbols & favorites management
│
├── 📂 models/                  ← Data Models
│   ├── __init__.py
│   └── market_model.py         ← Table data model
│
├── 📂 ui/                      ← Main UI Components
│   ├── __init__.py
│   ├── market_widget.py        ← Main widget with tabs
│   ├── market_table.py         ← Symbol table
│   ├── trade_panel.py          ← Trade interface
│   └── row_hover_delegate.py   ← Table styling
│
├── 📂 components/              ← Reusable Components
│   ├── __init__.py
│   └── tab_bar.py              ← Custom tab bar
│
├── 📂 widgets/                 ← Custom Widgets
│   ├── __init__.py
│   └── lot_preset_widget.py    ← Lot size presets
│
├── 📂 styles/                  ← Stylesheets (optional)
│
├── main.py                     ← App entry point
├── README.md                   ← Full documentation
├── requirements.txt            ← Dependencies
└── QUICKSTART.md              ← This file
```

## 🚀 Next Steps

1. **Implement Settings Dialog**
   - User preferences
   - Display options
   - Account settings

2. **Create Place Order Dialog**
   - Market/Limit orders
   - Stop loss/Take profit
   - Order confirmation

3. **Add Real-time Updates**
   - WebSocket connection
   - Price streaming
   - Auto-refresh

4. **Enhance Features**
   - Multiple watchlists
   - Price alerts
   - Trade history
   - Charts integration

---

**Questions? Check README.md for detailed documentation!**
