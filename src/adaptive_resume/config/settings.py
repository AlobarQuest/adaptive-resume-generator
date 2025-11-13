"""Application settings management."""

import json
from pathlib import Path
from typing import Optional
from adaptive_resume.utils.encryption import EncryptionManager


class Settings:
    """
    Manages application settings including secure API key storage.
    
    Settings are stored in ~/.adaptive_resume/settings.json
    API keys are encrypted using Fernet encryption.
    
    The API key is stored independently of whether AI enhancement is enabled.
    Users can toggle AI on/off without losing their stored key.
    """
    
    SETTINGS_FILE = Path.home() / ".adaptive_resume" / "settings.json"
    
    def __init__(self):
        """Initialize settings manager."""
        self.encryption = EncryptionManager()
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """
        Load settings from file.
        
        Returns:
            Settings dictionary
        """
        if not self.SETTINGS_FILE.exists():
            return self._default_settings()
        
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            # If file is corrupted, return defaults
            return self._default_settings()
    
    def _default_settings(self) -> dict:
        """
        Get default settings.
        
        Returns:
            Default settings dictionary
        """
        return {
            'ai_enhancement_enabled': False,
            'anthropic_api_key_encrypted': None,
            'theme': 'dark_blue',
            'auto_save': True,
            'recent_enhancements': []
        }
    
    def save(self):
        """Save settings to file."""
        # Ensure directory exists
        self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write settings
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def set_api_key(self, api_key: str):
        """
        Store encrypted API key.
        
        Note: This does NOT automatically enable AI enhancement.
        The key is stored independently so users can toggle AI on/off.
        
        Args:
            api_key: Anthropic API key to store
        """
        encrypted = self.encryption.encrypt(api_key)
        self.settings['anthropic_api_key_encrypted'] = encrypted
        # Don't auto-enable - let user control that separately
        self.save()
    
    def get_api_key(self) -> Optional[str]:
        """
        Retrieve and decrypt API key.
        
        Returns:
            Decrypted API key or None if not set
        """
        encrypted = self.settings.get('anthropic_api_key_encrypted')
        if not encrypted:
            return None
        
        try:
            return self.encryption.decrypt(encrypted)
        except Exception:
            # Decryption failed - key may be invalid
            return None
    
    def has_api_key(self) -> bool:
        """
        Check if an API key is stored (regardless of whether AI is enabled).
        
        Returns:
            True if API key exists in storage
        """
        return self.settings.get('anthropic_api_key_encrypted') is not None
    
    def clear_api_key(self):
        """Remove API key from storage."""
        self.settings['anthropic_api_key_encrypted'] = None
        # When clearing key, also disable AI (makes sense - can't use AI without key)
        self.settings['ai_enhancement_enabled'] = False
        self.save()
    
    @property
    def ai_enabled(self) -> bool:
        """
        Check if AI enhancement is currently enabled AND a key exists.
        
        Returns:
            True if both AI is enabled and API key exists
        """
        return (
            self.settings.get('ai_enhancement_enabled', False) 
            and self.settings.get('anthropic_api_key_encrypted') is not None
        )
    
    def get(self, key: str, default=None):
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """
        Set a setting value.
        
        Note: This does NOT automatically save to disk.
        Call save() after setting values.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
