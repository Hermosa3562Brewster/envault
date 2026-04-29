"""Snapshot management: save and restore named snapshots of vault state."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshots_dir(vault_path: Path) -> Path:
    return vault_path.parent / ".envault_snapshots" / vault_path.stem


def _index_path(vault_path: Path) -> Path:
    return _snapshots_dir(vault_path) / "index.json"


def _load_index(vault_path: Path) -> Dict[str, str]:
    idx = _index_path(vault_path)
    if not idx.exists():
        return {}
    return json.loads(idx.read_text())


def _save_index(vault_path: Path, index: Dict[str, str]) -> None:
    idx = _index_path(vault_path)
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(json.dumps(index, indent=2))


def create_snapshot(vault_path: Path, name: str) -> Path:
    """Copy the current vault file to a named snapshot. Returns snapshot path."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise SnapshotError(f"Vault file not found: {vault_path}")

    snap_dir = _snapshots_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    snap_file = snap_dir / f"{name}.vault"
    shutil.copy2(vault_path, snap_file)

    index = _load_index(vault_path)
    index[name] = timestamp
    _save_index(vault_path, index)

    return snap_file


def restore_snapshot(vault_path: Path, name: str) -> None:
    """Overwrite the vault file with a named snapshot."""
    vault_path = Path(vault_path)
    index = _load_index(vault_path)
    if name not in index:
        raise SnapshotError(f"Snapshot '{name}' not found.")

    snap_file = _snapshots_dir(vault_path) / f"{name}.vault"
    if not snap_file.exists():
        raise SnapshotError(f"Snapshot file missing for '{name}'.")

    shutil.copy2(snap_file, vault_path)


def list_snapshots(vault_path: Path) -> List[Dict[str, str]]:
    """Return a list of snapshots sorted by creation time (oldest first)."""
    index = _load_index(Path(vault_path))
    return sorted(
        [{"name": k, "created_at": v} for k, v in index.items()],
        key=lambda x: x["created_at"],
    )


def delete_snapshot(vault_path: Path, name: str) -> None:
    """Remove a named snapshot."""
    vault_path = Path(vault_path)
    index = _load_index(vault_path)
    if name not in index:
        raise SnapshotError(f"Snapshot '{name}' not found.")

    snap_file = _snapshots_dir(vault_path) / f"{name}.vault"
    if snap_file.exists():
        snap_file.unlink()

    del index[name]
    _save_index(vault_path, index)
