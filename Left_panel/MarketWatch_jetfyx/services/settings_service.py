"""
Settings Service - Manages application settings
"""
from PySide6.QtCore import QObject, Signal
from MarketWatch_jetfyx.config.app_config import AppConfig


class SettingsService(QObject):
    """Service for managing application settings"""
    
    settingsChanged = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self._settings = AppConfig.load()
    
    def get_settings(self):
        """Get all settings"""
        return self._settings.copy()
    
    def get(self, key, default=None):
        """Get a specific setting"""
        return self._settings.get(key, default)
    
    def update(self, settings):
        """Update settings"""
        self._settings.update(settings)
        AppConfig.save(self._settings)
        self.settingsChanged.emit(self._settings.copy())
    
    def set(self, key, value):
        """Set a specific setting"""
        self._settings[key] = value
        AppConfig.save(self._settings)
        self.settingsChanged.emit(self._settings.copy())
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self._settings = AppConfig.DEFAULT_CONFIG.copy()
        AppConfig.save(self._settings)
        self.settingsChanged.emit(self._settings.copy())
