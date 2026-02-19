"""
Formatting utilities
"""


def format_price(price, decimals=5):
    """Format price with specified decimals"""
    try:
        return f"{float(price):.{decimals}f}"
    except:
        return str(price)


def format_volume(volume):
    """Format volume/lot size"""
    try:
        return f"{float(volume):.2f}"
    except:
        return str(volume)


def format_percent(value):
    """Format percentage"""
    try:
        return f"{float(value):.2f}%"
    except:
        return str(value)
