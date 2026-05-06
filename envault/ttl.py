"""TTL (time-to-live) support for vault secrets.

Allows setting an expiry timestamp on a vault profile so that
envault can warn or refuse to load secrets past their expiry.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class TTLError(Exception):
    """Raised when a TTL operation fails."""


_TTL_FILENAME = ".ttl.json"


def _ttl_path(profile_dir: Path) -> Path:
    return profile_dir / _TTL_FILENAME


@dataclass
class TTLRecord:
    expires_at: float  # Unix timestamp
    note: str = ""

    def is_expired(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        return now >= self.expires_at

    def seconds_remaining(self, now: Optional[float] = None) -> float:
        if now is None:
            now = time.time()
        return max(0.0, self.expires_at - now)


def set_ttl(profile_dir: Path, expires_at: float, note: str = "") -> TTLRecord:
    """Persist a TTL record for the given profile directory."""
    profile_dir = Path(profile_dir)
    if not profile_dir.exists():
        raise TTLError(f"Profile directory not found: {profile_dir}")
    record = TTLRecord(expires_at=expires_at, note=note)
    _ttl_path(profile_dir).write_text(
        json.dumps({"expires_at": record.expires_at, "note": record.note})
    )
    return record


def get_ttl(profile_dir: Path) -> Optional[TTLRecord]:
    """Load the TTL record for a profile, or None if none is set."""
    path = _ttl_path(Path(profile_dir))
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return TTLRecord(expires_at=data["expires_at"], note=data.get("note", ""))


def clear_ttl(profile_dir: Path) -> bool:
    """Remove the TTL record for a profile. Returns True if one existed."""
    path = _ttl_path(Path(profile_dir))
    if path.exists():
        path.unlink()
        return True
    return False


def check_ttl(profile_dir: Path, now: Optional[float] = None) -> Optional[TTLRecord]:
    """Return the TTL record if it is expired, else None.

    Callers can use the return value to decide whether to block access.
    """
    record = get_ttl(profile_dir)
    if record is not None and record.is_expired(now=now):
        return record
    return None
