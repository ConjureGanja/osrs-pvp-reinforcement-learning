"""Secure credential storage for the OSRS RL GUI."""
import base64
import os
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional
import logging

from .error_handling import handle_exceptions, ConfigurationError

logger = logging.getLogger(__name__)


class SecureCredentialStore:
    """Secure storage for sensitive credentials using encryption."""
    
    def __init__(self):
        self._key_file = Path.home() / ".osrs_rl" / ".key"
        self._credentials_file = Path.home() / ".osrs_rl" / ".creds"
        self._key_file.parent.mkdir(exist_ok=True, mode=0o700)
        self._fernet = self._get_or_create_encryption_key()
    
    @handle_exceptions((Exception,), reraise=True)
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get existing encryption key or create a new one."""
        try:
            if self._key_file.exists():
                with open(self._key_file, 'rb') as f:
                    key = f.read()
                logger.info("Loaded existing encryption key")
            else:
                key = Fernet.generate_key()
                with open(self._key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions on key file
                os.chmod(self._key_file, 0o600)
                logger.info("Created new encryption key")
            
            return Fernet(key)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize encryption: {e}") from e
    
    @handle_exceptions((Exception,), reraise=True)
    def store_credentials(self, username: str, password: str) -> None:
        """Store encrypted credentials."""
        if not username.strip():
            raise ValueError("Username cannot be empty")
        
        try:
            credentials_data = f"{username}:{password}"
            encrypted_data = self._fernet.encrypt(credentials_data.encode())
            
            with open(self._credentials_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self._credentials_file, 0o600)
            
            logger.info("Credentials stored securely")
        except Exception as e:
            raise ConfigurationError(f"Failed to store credentials: {e}") from e
    
    @handle_exceptions((Exception,), reraise=False, default_return=None)
    def retrieve_credentials(self) -> Optional[tuple[str, str]]:
        """Retrieve and decrypt stored credentials."""
        if not self._credentials_file.exists():
            logger.debug("No credentials file found")
            return None
        
        try:
            with open(self._credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._fernet.decrypt(encrypted_data).decode()
            username, password = decrypted_data.split(':', 1)
            logger.info("Retrieved credentials successfully")
            return (username, password)
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None
    
    @handle_exceptions((Exception,), reraise=True)
    def clear_credentials(self) -> None:
        """Remove stored credentials."""
        try:
            if self._credentials_file.exists():
                self._credentials_file.unlink()
            logger.info("Credentials cleared")
        except Exception as e:
            raise ConfigurationError(f"Failed to clear credentials: {e}") from e