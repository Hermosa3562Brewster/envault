"""Cryptographic utilities for encrypting and decrypting .env file contents."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken


SALT_SIZE = 16
KDF_ITERATIONS = 390_000


def derive_key(master_key: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a master key string and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    raw_key = kdf.derive(master_key.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt(plaintext: str, master_key: str) -> bytes:
    """Encrypt plaintext using the master key.

    Returns a bytes blob: <salt (16 bytes)> + <fernet token>.
    """
    salt = os.urandom(SALT_SIZE)
    key = derive_key(master_key, salt)
    token = Fernet(key).encrypt(plaintext.encode("utf-8"))
    return salt + token


def decrypt(cipherblob: bytes, master_key: str) -> str:
    """Decrypt a blob produced by :func:`encrypt`.

    Raises:
        ValueError: if the master key is wrong or the data is corrupted.
    """
    if len(cipherblob) <= SALT_SIZE:
        raise ValueError("Invalid cipherblob: too short.")
    salt, token = cipherblob[:SALT_SIZE], cipherblob[SALT_SIZE:]
    key = derive_key(master_key, salt)
    try:
        return Fernet(key).decrypt(token).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid master key or corrupted data.") from exc
