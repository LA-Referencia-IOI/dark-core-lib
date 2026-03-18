"""Cryptography utilities for authority key storage."""

import hashlib
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_encryption_key(admin_private_key: str) -> bytes:
    """Derive a 32-byte AES key from the admin private key."""
    if admin_private_key.startswith("0x"):
        admin_private_key = admin_private_key[2:]
    key_bytes = bytes.fromhex(admin_private_key)
    return hashlib.sha256(key_bytes).digest()


def encrypt_private_key(private_key: str, admin_private_key: str) -> str:
    """Encrypt a private key with AES-256-GCM; returns hex(nonce+ciphertext)."""
    aes_key = derive_encryption_key(admin_private_key)
    aesgcm = AESGCM(aes_key)
    nonce = secrets.token_bytes(12)

    if private_key.startswith("0x"):
        private_key = private_key[2:]
    data = bytes.fromhex(private_key)

    ciphertext = aesgcm.encrypt(nonce, data, None)
    return (nonce + ciphertext).hex()


def decrypt_private_key(encrypted_hex: str, admin_private_key: str) -> str:
    """Decrypt hex(nonce+ciphertext) and return a 0x-prefixed key."""
    aes_key = derive_encryption_key(admin_private_key)
    aesgcm = AESGCM(aes_key)

    if encrypted_hex.startswith("0x"):
        encrypted_hex = encrypted_hex[2:]

    encrypted = bytes.fromhex(encrypted_hex)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    data = aesgcm.decrypt(nonce, ciphertext, None)

    return "0x" + data.hex()
