"""Sync vault files between environments using a shared directory (e.g. network share, cloud mount)."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.audit import record
from envault.profiles import load_index


SYNC_MANIFEST = ".envault_sync"


def _manifest_path(sync_dir: Path) -> Path:
    return sync_dir / SYNC_MANIFEST


def push(profile: str, vault_path: Path, sync_dir: Path) -> Path:
    """Copy a locked vault file to the shared sync directory.

    Returns the destination path.
    """
    sync_dir.mkdir(parents=True, exist_ok=True)
    dest = sync_dir / f"{profile}.vault"
    shutil.copy2(vault_path, dest)

    manifest = _load_manifest(sync_dir)
    manifest[profile] = {
        "pushed_at": datetime.now(timezone.utc).isoformat(),
        "size": dest.stat().st_size,
    }
    _save_manifest(sync_dir, manifest)

    record("push", profile, {"dest": str(dest)})
    return dest


def pull(profile: str, sync_dir: Path, vault_path: Path) -> Path:
    """Copy a vault file from the shared sync directory to the local vault path.

    Returns the local vault path.
    """
    src = sync_dir / f"{profile}.vault"
    if not src.exists():
        raise FileNotFoundError(f"No synced vault found for profile '{profile}' in {sync_dir}")

    vault_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, vault_path)

    record("pull", profile, {"src": str(src)})
    return vault_path


def list_remote(sync_dir: Path) -> dict[str, dict]:
    """Return the sync manifest entries from the shared directory."""
    return _load_manifest(sync_dir)


def _load_manifest(sync_dir: Path) -> dict:
    import json
    p = _manifest_path(sync_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_manifest(sync_dir: Path, data: dict) -> None:
    import json
    _manifest_path(sync_dir).write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
