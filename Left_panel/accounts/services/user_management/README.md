# User Management Microservice

This microservice handles user-related operations in a decoupled, maintainable manner.

## Structure

```
services/
└── user_management/
    ├── __init__.py          # Package initialization
    ├── models.py            # Pydantic data models
    └── service.py           # Core service logic
```

## Features

### Add User to Profile

Allows a primary user to add a secondary user to their profile.

**Endpoint**: `/Auth/add-user-to-profile`

**Request Model**:
```python
{
    "primaryUserId": int,
    "secondaryUserEmail": str,
    "secondaryUserPassword": str
}
```

**Response Model**:
```python
{
    "data": dict | None,
    "message": str | None,
    "statusCode": int | None
}
```

## Usage

```python
from services.user_management import UserManagementService
from api.config import API_BASE_URL

# Initialize the service
service = UserManagementService(API_BASE_URL, access_token="your_token")

# Add a user to profile
success, message, data = service.add_user_to_profile(
    primary_user_id=123,
    secondary_email="user@example.com",
    secondary_password="password123"
)

if success:
    print(f"Success: {message}")
else:
    print(f"Error: {message}")
```

## Design Principles

1. **Separation of Concerns**: Service logic is separated from UI code
2. **Type Safety**: Pydantic models ensure data validation
3. **Error Handling**: Comprehensive error handling with clear messages
4. **Logging**: Detailed logging for debugging
5. **Retry Logic**: Automatic retry for transient network errors
6. **Testability**: Easy to mock and test independently

## Authentication

The service supports Bearer token authentication. Pass the access token when initializing:

```python
service = UserManagementService(API_BASE_URL, access_token=token)
```

## Error Handling

The service returns a tuple of `(success, message, data)`:
- **success** (bool): Whether the operation succeeded
- **message** (str): Human-readable message
- **data** (dict | None): Response data if available

## Future Enhancements

- Add more user management operations
- Implement caching for frequently accessed data
- Add rate limiting
- Support batch operations


/* --- Merged from MarketWatch_jetfyx\README.md --- */
# MarketWatch Trading Application

A professional-grade trading application with symbol management, favorites, and real-time market data display.

## Project Structure

```
MarketWatch_jetfyx/
├── main.py                          # Application entry point
├── core/                            # Business logic & data management
│   ├── __init__.py
│   └── symbol_manager.py            # Manages symbols and favorites
├── models/                          # Data models
│   ├── __init__.py
│   └── market_model.py              # Table model for market data
├── ui/                              # Main UI components
│   ├── __init__.py
│   ├── market_widget.py             # Main market widget with tabs
│   ├── market_table.py              # Symbol table view
│   ├── trade_panel.py               # Expandable trade panel
│   └── row_hover_delegate.py        # Custom table delegate
├── components/                      # Reusable UI components
│   ├── __init__.py
│   └── tab_bar.py                   # Custom tab bar with settings
├── widgets/                         # Custom widgets
│   ├── __init__.py
│   └── lot_preset_widget.py         # Lot size preset buttons
└── styles/                          # Stylesheets (optional)
```

## Features

### 1. **Tabbed Interface**
- **Favourites Tab**: Shows only favorite symbols (default 7)
- **All Symbols Tab**: Shows all available symbols (33)
- **Settings Button**: Access application settings (⚙)

### 2. **Symbol Management**
- Add/remove favorites with star button (★/☆)
- Search symbols in real-time
- Toggle between favorite and non-favorite states
- Automatic count updates in tabs

### 3. **Trade Panel**
- Expandable row-level trade interface
- Buy/Sell buttons with live prices
- Lot size management with +/- controls
- Preset lot buttons (0.01, 0.10, 1.00)
- L (Low) and H (High) price indicators
- Quick actions: Favorite, Place Order, Info, Close

### 4. **Search Functionality**
- Real-time search across symbols
- Context-aware (searches within active tab)
- Clear visual feedback

## Code Organization

### Production-Level Structure

1. **`core/`** - Business Logic
   - `SymbolManager`: Central data management for symbols and favorites
   - Signals for reactive updates across the application

2. **`models/`** - Data Models
   - `MarketModel`: Qt table model for market data display
   - Separation of data from presentation

3. **`ui/`** - Main UI Components
   - `MarketWidget`: Main container with tabs and search
   - `MarketTable`: Symbol table with expandable rows
   - `TradePanel`: Detailed trading interface per symbol

4. **`components/`** - Reusable Components
   - `TabBar`: Custom tab bar with integrated settings button
   - Modular design for easy reuse

5. **`widgets/`** - Custom Widgets
   - `LotPresetWidget`: Specialized lot size selector
   - Self-contained functionality

## Usage

### Running the Application

```bash
python main.py
```

### Adding New Symbols

Edit `core/symbol_manager.py`:

```python
self._all_symbols = [
    ("SYMBOLNAME", "sell_price", "buy_price"),
    # Add more symbols...
]
```

### Customizing Favorites

Default favorites are set in `SymbolManager.__init__()`:

```python
self._favorites = set(["EURUSD", "GBPUSD", ...])
```

## Key Classes

### `SymbolManager`
Central manager for all symbol data and favorite status.

**Methods:**
- `get_all_symbols()` - Returns all symbols
- `get_favorites()` - Returns only favorite symbols
- `toggle_favorite(symbol)` - Toggle favorite status
- `search_symbols(query)` - Search symbols by name

**Signals:**
- `favoritesChanged` - Emitted when favorites list changes

### `TabBar`
Custom tab widget with settings button.

**Methods:**
- `update_counts(fav, all)` - Update tab counters
- `set_current_tab(index)` - Programmatically change tab

**Signals:**
- `tabChanged(int)` - Emitted when active tab changes
- `settingsClicked()` - Emitted when settings button clicked

### `MarketTable`
Table view with expandable trade panels.

**Methods:**
- `set_symbols(data)` - Update displayed symbols
- `toggle_row(index)` - Expand/collapse trade panel

**Signals:**
- `favoriteToggled(str, bool)` - Emitted when favorite changed

### `TradePanel`
Expandable panel for trading operations.

**Features:**
- Buy/Sell buttons with live prices
- Lot management with presets
- Favorite toggle
- Place order button
- Close button

## Dependencies

- PySide6 (Qt for Python)
- Python 3.8+

## Future Enhancements

1. Settings dialog implementation
2. Place order dialog with order types
3. Real-time price updates
4. Historical charts
5. Trade history tracking
6. Custom watchlists
7. Price alerts
8. Multi-account support

## Maintainability

The code is organized for easy maintenance:
- **Separation of Concerns**: Business logic, models, and UI are separated
- **Modular Design**: Each component is self-contained
- **Clear Naming**: Descriptive names for classes and methods
- **Documentation**: Docstrings for all major classes and methods
- **Signals/Slots**: Reactive programming for loose coupling
- **Production Ready**: Scalable architecture for future features




/* --- Merged from backup\duplicates_20260124_123934\accounts\services\user_management\README.md --- */
# User Management Microservice

This microservice handles user-related operations in a decoupled, maintainable manner.

## Structure

```
services/
└── user_management/
    ├── __init__.py          # Package initialization
    ├── models.py            # Pydantic data models
    └── service.py           # Core service logic
```

## Features

### Add User to Profile

Allows a primary user to add a secondary user to their profile.

**Endpoint**: `/Auth/add-user-to-profile`

**Request Model**:
```python
{
    "primaryUserId": int,
    "secondaryUserEmail": str,
    "secondaryUserPassword": str
}
```

**Response Model**:
```python
{
    "data": dict | None,
    "message": str | None,
    "statusCode": int | None
}
```

## Usage

```python
from services.user_management import UserManagementService
from api.config import API_BASE_URL

# Initialize the service
service = UserManagementService(API_BASE_URL, access_token="your_token")

# Add a user to profile
success, message, data = service.add_user_to_profile(
    primary_user_id=123,
    secondary_email="user@example.com",
    secondary_password="password123"
)

if success:
    print(f"Success: {message}")
else:
    print(f"Error: {message}")
```

## Design Principles

1. **Separation of Concerns**: Service logic is separated from UI code
2. **Type Safety**: Pydantic models ensure data validation
3. **Error Handling**: Comprehensive error handling with clear messages
4. **Logging**: Detailed logging for debugging
5. **Retry Logic**: Automatic retry for transient network errors
6. **Testability**: Easy to mock and test independently

## Authentication

The service supports Bearer token authentication. Pass the access token when initializing:

```python
service = UserManagementService(API_BASE_URL, access_token=token)
```

## Error Handling

The service returns a tuple of `(success, message, data)`:
- **success** (bool): Whether the operation succeeded
- **message** (str): Human-readable message
- **data** (dict | None): Response data if available

## Future Enhancements

- Add more user management operations
- Implement caching for frequently accessed data
- Add rate limiting
- Support batch operations




/* --- Merged from backup\duplicates_20260124_123934\MarketWatch_jetfyx\README.md --- */
# MarketWatch Trading Application

A professional-grade trading application with symbol management, favorites, and real-time market data display.

## Project Structure

```
MarketWatch_jetfyx/
├── main.py                          # Application entry point
├── core/                            # Business logic & data management
│   ├── __init__.py
│   └── symbol_manager.py            # Manages symbols and favorites
├── models/                          # Data models
│   ├── __init__.py
│   └── market_model.py              # Table model for market data
├── ui/                              # Main UI components
│   ├── __init__.py
│   ├── market_widget.py             # Main market widget with tabs
│   ├── market_table.py              # Symbol table view
│   ├── trade_panel.py               # Expandable trade panel
│   └── row_hover_delegate.py        # Custom table delegate
├── components/                      # Reusable UI components
│   ├── __init__.py
│   └── tab_bar.py                   # Custom tab bar with settings
├── widgets/                         # Custom widgets
│   ├── __init__.py
│   └── lot_preset_widget.py         # Lot size preset buttons
└── styles/                          # Stylesheets (optional)
```

## Features

### 1. **Tabbed Interface**
- **Favourites Tab**: Shows only favorite symbols (default 7)
- **All Symbols Tab**: Shows all available symbols (33)
- **Settings Button**: Access application settings (⚙)

### 2. **Symbol Management**
- Add/remove favorites with star button (★/☆)
- Search symbols in real-time
- Toggle between favorite and non-favorite states
- Automatic count updates in tabs

### 3. **Trade Panel**
- Expandable row-level trade interface
- Buy/Sell buttons with live prices
- Lot size management with +/- controls
- Preset lot buttons (0.01, 0.10, 1.00)
- L (Low) and H (High) price indicators
- Quick actions: Favorite, Place Order, Info, Close

### 4. **Search Functionality**
- Real-time search across symbols
- Context-aware (searches within active tab)
- Clear visual feedback

## Code Organization

### Production-Level Structure

1. **`core/`** - Business Logic
   - `SymbolManager`: Central data management for symbols and favorites
   - Signals for reactive updates across the application

2. **`models/`** - Data Models
   - `MarketModel`: Qt table model for market data display
   - Separation of data from presentation

3. **`ui/`** - Main UI Components
   - `MarketWidget`: Main container with tabs and search
   - `MarketTable`: Symbol table with expandable rows
   - `TradePanel`: Detailed trading interface per symbol

4. **`components/`** - Reusable Components
   - `TabBar`: Custom tab bar with integrated settings button
   - Modular design for easy reuse

5. **`widgets/`** - Custom Widgets
   - `LotPresetWidget`: Specialized lot size selector
   - Self-contained functionality

## Usage

### Running the Application

```bash
python main.py
```

### Adding New Symbols

Edit `core/symbol_manager.py`:

```python
self._all_symbols = [
    ("SYMBOLNAME", "sell_price", "buy_price"),
    # Add more symbols...
]
```

### Customizing Favorites

Default favorites are set in `SymbolManager.__init__()`:

```python
self._favorites = set(["EURUSD", "GBPUSD", ...])
```

## Key Classes

### `SymbolManager`
Central manager for all symbol data and favorite status.

**Methods:**
- `get_all_symbols()` - Returns all symbols
- `get_favorites()` - Returns only favorite symbols
- `toggle_favorite(symbol)` - Toggle favorite status
- `search_symbols(query)` - Search symbols by name

**Signals:**
- `favoritesChanged` - Emitted when favorites list changes

### `TabBar`
Custom tab widget with settings button.

**Methods:**
- `update_counts(fav, all)` - Update tab counters
- `set_current_tab(index)` - Programmatically change tab

**Signals:**
- `tabChanged(int)` - Emitted when active tab changes
- `settingsClicked()` - Emitted when settings button clicked

### `MarketTable`
Table view with expandable trade panels.

**Methods:**
- `set_symbols(data)` - Update displayed symbols
- `toggle_row(index)` - Expand/collapse trade panel

**Signals:**
- `favoriteToggled(str, bool)` - Emitted when favorite changed

### `TradePanel`
Expandable panel for trading operations.

**Features:**
- Buy/Sell buttons with live prices
- Lot management with presets
- Favorite toggle
- Place order button
- Close button

## Dependencies

- PySide6 (Qt for Python)
- Python 3.8+

## Future Enhancements

1. Settings dialog implementation
2. Place order dialog with order types
3. Real-time price updates
4. Historical charts
5. Trade history tracking
6. Custom watchlists
7. Price alerts
8. Multi-account support

## Maintainability

The code is organized for easy maintenance:
- **Separation of Concerns**: Business logic, models, and UI are separated
- **Modular Design**: Each component is self-contained
- **Clear Naming**: Descriptive names for classes and methods
- **Documentation**: Docstrings for all major classes and methods
- **Signals/Slots**: Reactive programming for loose coupling
- **Production Ready**: Scalable architecture for future features


