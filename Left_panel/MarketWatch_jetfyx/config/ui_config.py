"""
UI Configuration - All UI-related constants and settings
"""

# Colors
COLORS = {
    'primary': '#1976d2',
    'primary_light': '#bbdefb',
    'primary_dark': '#0d47a1',
    'success': '#4caf50',
    'success_dark': '#45a049',
    'danger': '#e53935',
    'danger_dark': '#c62828',
    'background': '#ffffff',
    'background_alt': '#f9f9f9',
    'border': '#ddd',
    'text': '#333',
    'text_light': '#666',
    'text_lighter': '#999',
}

# Sizes
SIZES = {
    'button_small': (22, 22),
    'button_medium': (40, 40),
    'button_large': (130, 60),
    'input_height': 40,
    'panel_height': 120,
    'dialog_width': 710,
    'dialog_height': 550,
}

# Fonts
FONTS = {
    'title': {'size': 20, 'weight': 'bold'},
    'subtitle': {'size': 16, 'weight': 'bold'},
    'body': {'size': 13, 'weight': 'normal'},
    'small': {'size': 11, 'weight': 'normal'},
}

# Styles
BUTTON_STYLES = {
    'buy': f"""
        QPushButton {{
            background: {COLORS['success']};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {COLORS['success_dark']};
        }}
    """,
    'sell': f"""
        QPushButton {{
            background: {COLORS['danger']};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {COLORS['danger_dark']};
        }}
    """,
    'standard': f"""
        QPushButton {{
            background: #f5f5f5;
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background: #e0e0e0;
        }}
    """,
}

INPUT_STYLE = f"""
    QLineEdit {{
        padding: 8px;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
    }}
"""
