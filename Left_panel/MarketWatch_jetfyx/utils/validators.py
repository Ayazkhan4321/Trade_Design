"""
Validation utilities
"""


def validate_lot_size(lot_size, min_lot=0.01, max_lot=100.0):
    """Validate lot size"""
    try:
        lot = float(lot_size)
        return min_lot <= lot <= max_lot
    except:
        return False


def validate_price(price):
    """Validate price value"""
    try:
        p = float(price)
        return p > 0
    except:
        return False
