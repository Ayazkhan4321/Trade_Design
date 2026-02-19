"""
Application Configuration
"""
import json
import os


class AppConfig:
    """Application configuration manager"""
    
    CONFIG_FILE = "app_config.json"
    
    DEFAULT_CONFIG = {
        'advance_view': False,
        'one_click_trade': False,
        'default_lot': 0.01,
        'default_lot_enabled': False,
        'window_width': 420,
        'window_height': 600,
        'theme': 'light'
    }
    
    @classmethod
    def load(cls):
        """Load configuration from file"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save(cls, config):
        """Save configuration to file"""
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @classmethod
    def get(cls, key, default=None):
        """Get a configuration value"""
        config = cls.load()
        return config.get(key, default)
    
    @classmethod
    def set(cls, key, value):
        """Set a configuration value"""
        config = cls.load()
        config[key] = value
        cls.save(config)
