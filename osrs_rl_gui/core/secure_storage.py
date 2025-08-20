"""Secure credential storage for the OSRS RL GUI."""
import base64
import os
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecureCredentialStore:
    """Secure storage for sensitive credentials using encryption."""
    
    def __init__(self):
        self._key_file = Path.home() / ".osrs_rl" / ".key"
        self._credentials_file = Path.home() / ".osrs_rl" / ".creds"
        self._key_file.parent.mkdir(exist_ok=True, mode=0o700)
        self._fernet = self._get_or_create_encryption_key()
    
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get existing encryption key or create a new one."""
        if self._key_file.exists():
            with open(self._key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self._key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions on key file
            os.chmod(self._key_file, 0o600)
        
        return Fernet(key)
    
    def store_credentials(self, username: str, password: str) -> None:
        """Store encrypted credentials."""
        try:
            credentials_data = f"{username}:{password}"
            encrypted_data = self._fernet.encrypt(credentials_data.encode())
            
            with open(self._credentials_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self._credentials_file, 0o600)
            
            logger.info("Credentials stored securely")
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            raise
    
    def retrieve_credentials(self) -> Optional[tuple[str, str]]:
        """Retrieve and decrypt stored credentials."""
        if not self._credentials_file.exists():
            return None
        
        try:
            with open(self._credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._fernet.decrypt(encrypted_data).decode()
            username, password = decrypted_data.split(':', 1)
            return (username, password)
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None
    
    def clear_credentials(self) -> None:
        """Remove stored credentials."""
        try:
            if self._credentials_file.exists():
                self._credentials_file.unlink()
            logger.info("Credentials cleared")
        except Exception as e:
            logger.error(f"Failed to clear credentials: {e}")
            raise