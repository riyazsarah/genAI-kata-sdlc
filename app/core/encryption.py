"""Encryption utilities for sensitive data using Fernet (AES-128)."""

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors."""

    pass


@lru_cache
def _get_fernet() -> Fernet:
    """Get a cached Fernet instance with the encryption key.

    Returns:
        Fernet instance for encryption/decryption.

    Raises:
        EncryptionError: If ENCRYPTION_KEY is not set or invalid.
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise EncryptionError(
            "ENCRYPTION_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        return Fernet(key.encode())
    except Exception as e:
        raise EncryptionError(f"Invalid ENCRYPTION_KEY: {e}") from e


def encrypt_data(plaintext: str) -> str:
    """Encrypt sensitive data.

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded encrypted string.

    Raises:
        EncryptionError: If encryption fails.
    """
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt_data(ciphertext: str) -> str:
    """Decrypt sensitive data.

    Args:
        ciphertext: Base64-encoded encrypted string.

    Returns:
        Decrypted plaintext string.

    Raises:
        EncryptionError: If decryption fails.
    """
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except InvalidToken as e:
        raise EncryptionError("Invalid or corrupted encrypted data") from e
    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Decryption failed: {e}") from e


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        A new base64-encoded Fernet key.
    """
    return Fernet.generate_key().decode()
