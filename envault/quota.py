"""Quota management: limit the number of secrets stored per profile."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_QUOTA = 100


class QuotaError(Exception):
    """Raised when a quota operation fails."""


def _quota_path(profile_dir: Path) -> Path:
    return profile_dir / ".quota.json"


@dataclass
class QuotaRecord:
    limit: int = DEFAULT_QUOTA
    overrides: Dict[str, int] = field(default_factory=dict)


def load_quota(profile_dir: Path) -> QuotaRecord:
    """Load quota settings for a profile directory."""
    path = _quota_path(profile_dir)
    if not path.exists():
        return QuotaRecord()
    try:
        data = json.loads(path.read_text())
        return QuotaRecord(
            limit=int(data.get("limit", DEFAULT_QUOTA)),
            overrides={k: int(v) for k, v in data.get("overrides", {}).items()},
        )
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        raise QuotaError(f"Corrupt quota file: {path}") from exc


def save_quota(profile_dir: Path, record: QuotaRecord) -> None:
    """Persist quota settings for a profile directory."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    _quota_path(profile_dir).write_text(
        json.dumps({"limit": record.limit, "overrides": record.overrides}, indent=2)
    )


def set_limit(profile_dir: Path, limit: int, key: Optional[str] = None) -> None:
    """Set the global limit or a per-key override."""
    if limit < 1:
        raise QuotaError("Quota limit must be at least 1.")
    record = load_quota(profile_dir)
    if key:
        record.overrides[key] = limit
    else:
        record.limit = limit
    save_quota(profile_dir, record)


def remove_override(profile_dir: Path, key: str) -> None:
    """Remove a per-key quota override."""
    record = load_quota(profile_dir)
    if key not in record.overrides:
        raise QuotaError(f"No override found for key '{key}'.")
    del record.overrides[key]
    save_quota(profile_dir, record)


def check_quota(profile_dir: Path, env: dict, key: Optional[str] = None) -> bool:
    """Return True if adding one more secret would exceed the quota."""
    record = load_quota(profile_dir)
    limit = record.overrides.get(key, record.limit) if key else record.limit
    return len(env) >= limit


def effective_limit(profile_dir: Path, key: Optional[str] = None) -> int:
    """Return the effective limit for the profile (or a specific key)."""
    record = load_quota(profile_dir)
    if key:
        return record.overrides.get(key, record.limit)
    return record.limit
