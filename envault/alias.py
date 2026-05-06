"""Profile alias management — map short names to full profile identifiers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _alias_path(base_dir: Path) -> Path:
    return base_dir / ".envault" / "aliases.json"


def load_aliases(base_dir: Path) -> Dict[str, str]:
    """Return the alias→profile mapping, or {} if none exists."""
    path = _alias_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AliasError(f"Corrupt alias file: {path}") from exc
    if not isinstance(data, dict):
        raise AliasError(f"Alias file must contain a JSON object: {path}")
    return {str(k): str(v) for k, v in data.items()}


def save_aliases(base_dir: Path, aliases: Dict[str, str]) -> None:
    """Persist the alias mapping to disk."""
    path = _alias_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aliases, indent=2, sort_keys=True))


def set_alias(base_dir: Path, alias: str, profile: str) -> None:
    """Create or overwrite *alias* pointing to *profile*."""
    alias = alias.strip()
    if not alias:
        raise AliasError("Alias name must not be blank.")
    if alias == profile:
        raise AliasError("Alias must differ from the profile name.")
    aliases = load_aliases(base_dir)
    aliases[alias] = profile
    save_aliases(base_dir, aliases)


def remove_alias(base_dir: Path, alias: str) -> None:
    """Delete *alias*; raises AliasError if it does not exist."""
    aliases = load_aliases(base_dir)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    del aliases[alias]
    save_aliases(base_dir, aliases)


def resolve(base_dir: Path, name: str) -> str:
    """Return the profile name for *name*, resolving an alias if present."""
    aliases = load_aliases(base_dir)
    return aliases.get(name, name)


def list_aliases(base_dir: Path) -> Dict[str, str]:
    """Return all defined aliases (alias → profile)."""
    return load_aliases(base_dir)
