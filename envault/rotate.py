"""Key rotation: re-encrypt a vault under a new master key."""

from __future__ import annotations

from pathlib import Path

from .crypto import decrypt, encrypt
from .vault import load_vault, save_vault
from .audit import record


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_vault(
    vault_path: Path | str,
    old_key: str,
    new_key: str,
    *,
    profile: str = "default",
) -> None:
    """Decrypt *vault_path* with *old_key* and re-encrypt it with *new_key*.

    The vault file is updated in-place.  An audit entry is written on success.

    Raises
    ------
    RotationError
        If the old key is wrong or the vault file does not exist.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise RotationError(f"Vault file not found: {vault_path}")

    try:
        env_vars = load_vault(vault_path, old_key)
    except ValueError as exc:
        raise RotationError("Old key is incorrect; cannot decrypt vault.") from exc

    save_vault(env_vars, vault_path, new_key)
    record(
        vault_path.parent,
        profile,
        "rotate",
        {"vault": str(vault_path)},
    )


def verify_key(vault_path: Path | str, key: str) -> bool:
    """Return *True* if *key* can successfully decrypt *vault_path*."""
    try:
        load_vault(Path(vault_path), key)
        return True
    except (ValueError, FileNotFoundError):
        return False
