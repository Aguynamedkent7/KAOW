"""Encryption helpers — basic data encryption for screenshots and logs.

Phase 1: Simple XOR-based obfuscation placeholder.
Phase 2: Replace with proper AES-GCM encryption using derived keys.
"""

from __future__ import annotations

import base64
import hashlib
import logging

logger = logging.getLogger(__name__)


def derive_key(secret: str, salt: bytes = b"kaow-salt-v1") -> bytes:
    """Derive a 32-byte key from a secret string using SHA-256.

    Args:
        secret: The secret passphrase.
        salt: Salt bytes for key derivation.

    Returns:
        32-byte derived key.
    """
    return hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 100_000)


def encrypt_data(data: bytes, secret: str) -> str:
    """Encrypt data using XOR with derived key (Phase 1 placeholder).

    WARNING: This is NOT secure encryption. Use for development only.
    Phase 2 will implement proper AES-GCM.

    Args:
        data: Raw bytes to encrypt.
        secret: Secret passphrase for key derivation.

    Returns:
        Base64-encoded encrypted data.
    """
    key = derive_key(secret)
    key_len = len(key)
    encrypted = bytes(b ^ key[i % key_len] for i, b in enumerate(data))
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_data(encrypted_b64: str, secret: str) -> bytes:
    """Decrypt data encrypted with encrypt_data.

    WARNING: This is NOT secure encryption. Use for development only.

    Args:
        encrypted_b64: Base64-encoded encrypted data.
        secret: Secret passphrase for key derivation.

    Returns:
        Decrypted raw bytes.
    """
    key = derive_key(secret)
    data = base64.b64decode(encrypted_b64)
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))
