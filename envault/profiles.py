"""Profile management for envault — supports named environments (dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PROFILE = "default"
PROFILE_INDEX_FILE = ".envault_profiles.json"


def _index_path(base_dir: Path) -> Path:
    return base_dir / PROFILE_INDEX_FILE


def load_index(base_dir: Path) -> Dict[str, str]:
    """Return mapping of profile_name -> vault filename."""
    index_file = _index_path(base_dir)
    if not index_file.exists():
        return {}
    with index_file.open("r") as fh:
        return json.load(fh)


def save_index(base_dir: Path, index: Dict[str, str]) -> None:
    """Persist the profile index to disk."""
    with _index_path(base_dir).open("w") as fh:
        json.dump(index, fh, indent=2)


def register_profile(base_dir: Path, profile: str, vault_filename: str) -> None:
    """Add or update a profile entry in the index."""
    index = load_index(base_dir)
    index[profile] = vault_filename
    save_index(base_dir, index)


def remove_profile(base_dir: Path, profile: str) -> bool:
    """Remove a profile from the index. Returns True if it existed."""
    index = load_index(base_dir)
    if profile not in index:
        return False
    del index[profile]
    save_index(base_dir, index)
    return True


def vault_filename_for(profile: str) -> str:
    """Return the conventional vault filename for a given profile."""
    if profile == DEFAULT_PROFILE:
        return ".env.vault"
    return f".env.{profile}.vault"


def list_profiles(base_dir: Path) -> List[str]:
    """Return sorted list of registered profile names."""
    return sorted(load_index(base_dir).keys())


def resolve_vault_path(base_dir: Path, profile: str) -> Optional[Path]:
    """Return the vault Path for a profile, or None if not registered."""
    index = load_index(base_dir)
    if profile not in index:
        return None
    return base_dir / index[profile]
