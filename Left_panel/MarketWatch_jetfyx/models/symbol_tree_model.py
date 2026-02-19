from PySide6.QtCore import Qt


class SymbolTreeModel:
    """Model for managing symbol tree data"""
    
    CATEGORIES = {
        'Majors': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
        'Metals': ['XAU', 'XAG', 'GOLD', 'SILVER'],
        'ENERGY': ['OIL', 'WTI', 'BRENT', 'USOIL', 'UKOIL'],
        'CRYPTO': ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM'],
        'Minors': []  # Everything else
    }
    
    @staticmethod
    def categorize_symbols(symbols):
        """Organize symbols into categories"""
        categorized = {
            'Majors': [],
            'Minors': [],
            'Metals': [],
            'ENERGY': [],
            'CRYPTO': []
        }
        
        for symbol in symbols:
            symbol_name = symbol[0]
            category_found = False
            
            # Check each category
            for category, keywords in SymbolTreeModel.CATEGORIES.items():
                if category == 'Minors':
                    continue
                    
                if any(keyword in symbol_name for keyword in keywords):
                    categorized[category].append(symbol)
                    category_found = True
                    break
            
            # If no category found, add to Minors
            if not category_found:
                # Check if it's a forex pair
                if any(curr in symbol_name for curr in ['EUR', 'GBP', 'USD', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']):
                    categorized['Minors'].append(symbol)
                else:
                    categorized['Minors'].append(symbol)
        
        return categorized
