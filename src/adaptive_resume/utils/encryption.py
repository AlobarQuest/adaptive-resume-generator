"""Encryption utilities for secure data storage."""

from cryptography.fernet import Fernet
from pathlib import Path
import base64
import os


class EncryptionManager:
    """Manages encryption for sensitive data like API keys."""
    
    KEY_FILE = Path.home() / ".adaptive_resume" / ".key"
    
    def __init__(self):
        """Initialize encryption manager with existing or new key."""
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """
        Get existing encryption key or create a new one.
        
        Returns:
            Encryption key as bytes
        """
        if self.KEY_FILE.exists():
            with open(self.KEY_FILE, 'rb') as f:
                return f.read()
        
        # Create new key
        key = Fernet.generate_key()
        
        # Ensure directory exists
        self.KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write key to file
        with open(self.KEY_FILE, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (owner read/write only)
        # This works on both Windows and Unix-like systems
        try:
            os.chmod(self.KEY_FILE, 0o600)
        except Exception:
            # On Windows, permissions work differently, but we tried
            pass
        
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted plain text string
        """
        decoded = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
