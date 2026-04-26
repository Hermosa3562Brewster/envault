"""Core vault operations: lock/unlock .env files, with optional profile support."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from envault.crypto import encrypt, decrypt
from envault import profiles as prof


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines; skip blanks and comments."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _serialize_env(env: Dict[str, str]) -> str:
    """Serialize a dict back to KEY=VALUE text."""
    return "\n".join(f"{k}={v}" for k, v in env.items()) + "\n"


# ---------------------------------------------------------------------------
# Vault I/O
# ---------------------------------------------------------------------------

def save_vault(vault_path: Path, cipherblob: bytes) -> None:
    vault_path.write_bytes(cipherblob)


def load_vault(vault_path: Path) -> bytes:
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")
    return vault_path.read_bytes()


# ---------------------------------------------------------------------------
# High-level operations
# ---------------------------------------------------------------------------

def lock(
    env_path: Path,
    password: str,
    vault_path: Optional[Path] = None,
    profile: str = prof.DEFAULT_PROFILE,
    base_dir: Optional[Path] = None,
) -> Path:
    """Encrypt *env_path* and write a vault file. Returns the vault path."""
    plaintext = env_path.read_bytes()
    cipherblob = encrypt(password, plaintext)

    _base = base_dir or env_path.parent
    if vault_path is None:
        vault_path = _base / prof.vault_filename_for(profile)

    save_vault(vault_path, cipherblob)
    prof.register_profile(_base, profile, vault_path.name)
    return vault_path


def unlock(
    vault_path: Path,
    password: str,
    env_path: Optional[Path] = None,
    profile: str = prof.DEFAULT_PROFILE,
    base_dir: Optional[Path] = None,
) -> Path:
    """Decrypt *vault_path* and write the .env file. Returns the env path."""
    cipherblob = load_vault(vault_path)
    plaintext = decrypt(password, cipherblob)  # raises ValueError on bad key

    _base = base_dir or vault_path.parent
    if env_path is None:
        suffix = "" if profile == prof.DEFAULT_PROFILE else f".{profile}"
        env_path = _base / f".env{suffix}"

    env_path.write_bytes(plaintext)
    return env_path


def view(
    vault_path: Path,
    password: str,
) -> Dict[str, str]:
    """Decrypt and return the env vars without writing to disk."""
    cipherblob = load_vault(vault_path)
    plaintext = decrypt(password, cipherblob)
    return _parse_env(plaintext.decode())
