"""Encryption utilities for token storage"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)


class Encryptor:
    """AES-256 encryption using Fernet symmetric encryption."""

    def __init__(self, key: str):
        """
        Initialize encryptor with encryption key.

        Args:
            key: 32-byte encryption key (URL-safe base64 encoded)
        """
        if len(key) < 32:
            raise ValueError("Encryption key must be at least 32 bytes")

        # Ensure key is 32 bytes (Fernet requirement)
        key_bytes = key.encode()[:32].ljust(32, b'\0')

        # Derive Fernet-compatible key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tool-plaid-salt',
            iterations=100000,
            backend=default_backend(),
        )
        derived_key = kdf.derive(key_bytes)
        self.fernet = Fernet(base64.urlsafe_b64encode(derived_key))

        logger.info("Encryptor initialized")

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.

        Args:
            data: Plain text string to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted plain text string
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
