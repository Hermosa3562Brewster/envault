"""Audit log for vault operations (lock, unlock, view, rotate)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_AUDIT_DIR = Path.home() / ".envault" / "audit"
ACTIONS = {"lock", "unlock", "view", "rotate", "profile_add", "profile_remove"}


def _audit_path(profile: str, audit_dir: Path = DEFAULT_AUDIT_DIR) -> Path:
    """Return the audit log path for a given profile."""
    return audit_dir / f"{profile}.log"


def record(
    profile: str,
    action: str,
    details: Dict[str, Any] | None = None,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
) -> None:
    """Append a timestamped audit entry for *action* on *profile*."""
    if action not in ACTIONS:
        raise ValueError(f"Unknown audit action: {action!r}. Must be one of {ACTIONS}.")

    audit_dir.mkdir(parents=True, exist_ok=True)
    path = _audit_path(profile, audit_dir)

    entry: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "profile": profile,
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
    }
    if details:
        entry["details"] = details

    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_log(
    profile: str,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
    limit: int | None = None,
) -> List[Dict[str, Any]]:
    """Return audit entries for *profile*, newest-last. Optionally cap at *limit*."""
    path = _audit_path(profile, audit_dir)
    if not path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    if limit is not None:
        entries = entries[-limit:]
    return entries


def clear_log(profile: str, audit_dir: Path = DEFAULT_AUDIT_DIR) -> None:
    """Delete the audit log for *profile*."""
    path = _audit_path(profile, audit_dir)
    if path.exists():
        path.unlink()
