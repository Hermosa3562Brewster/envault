"""Pin management: lock a vault to a specific key fingerprint to detect key rotation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pin_path(profile_dir: Path) -> Path:
    return profile_dir / "pin.json"


def _fingerprint(master_key: str) -> str:
    """Return a short SHA-256 hex digest of the master key."""
    return hashlib.sha256(master_key.encode()).hexdigest()[:16]


def pin_key(profile_dir: Path, master_key: str) -> str:
    """Store a fingerprint of *master_key* for *profile_dir*.

    Returns the fingerprint that was saved.
    """
    fp = _fingerprint(master_key)
    record = {"fingerprint": fp}
    _pin_path(profile_dir).write_text(json.dumps(record))
    return fp


def get_pin(profile_dir: Path) -> Optional[str]:
    """Return the stored fingerprint, or *None* if no pin exists."""
    p = _pin_path(profile_dir)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return data.get("fingerprint")
    except (json.JSONDecodeError, OSError) as exc:
        raise PinError(f"Could not read pin file: {exc}") from exc


def check_pin(profile_dir: Path, master_key: str) -> bool:
    """Return *True* if *master_key* matches the stored pin.

    Returns *True* when no pin is set (unpinned profiles always pass).
    """
    stored = get_pin(profile_dir)
    if stored is None:
        return True
    return _fingerprint(master_key) == stored


def remove_pin(profile_dir: Path) -> bool:
    """Delete the pin file if it exists.  Returns *True* if a file was removed."""
    p = _pin_path(profile_dir)
    if p.exists():
        p.unlink()
        return True
    return False
