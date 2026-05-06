"""Tag management for vault profiles.

Allows profiles to be tagged with arbitrary labels (e.g. 'production',
'staging', 'team-backend') so they can be grouped and filtered.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(profile_dir: Path) -> Path:
    return profile_dir / ".envault" / "tags.json"


def load_tags(profile_dir: Path) -> List[str]:
    """Return the list of tags for a profile directory.

    Returns an empty list when no tags file exists.
    """
    path = _tags_path(profile_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            raise TagError(f"Corrupt tags file: {path}")
        return [str(t) for t in data]
    except json.JSONDecodeError as exc:
        raise TagError(f"Invalid JSON in tags file: {path}") from exc


def save_tags(profile_dir: Path, tags: List[str]) -> None:
    """Persist *tags* for the given profile directory."""
    path = _tags_path(profile_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(tags)), indent=2))


def add_tag(profile_dir: Path, tag: str) -> List[str]:
    """Add *tag* to the profile and return the updated tag list."""
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must not be empty.")
    tags = load_tags(profile_dir)
    if tag not in tags:
        tags.append(tag)
    save_tags(profile_dir, tags)
    return sorted(set(tags))


def remove_tag(profile_dir: Path, tag: str) -> List[str]:
    """Remove *tag* from the profile and return the updated tag list.

    Raises TagError when the tag is not present.
    """
    tags = load_tags(profile_dir)
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on profile.")
    tags.remove(tag)
    save_tags(profile_dir, tags)
    return sorted(tags)


def profiles_by_tag(base_dir: Path, tag: str) -> List[str]:
    """Return profile names inside *base_dir* that carry *tag*."""
    matches: List[str] = []
    if not base_dir.exists():
        return matches
    for child in sorted(base_dir.iterdir()):
        if child.is_dir():
            if tag in load_tags(child):
                matches.append(child.name)
    return matches


def all_tags(base_dir: Path) -> Dict[str, List[str]]:
    """Return a mapping of profile_name -> tags for every profile in *base_dir*."""
    result: Dict[str, List[str]] = {}
    if not base_dir.exists():
        return result
    for child in sorted(base_dir.iterdir()):
        if child.is_dir():
            tags = load_tags(child)
            if tags:
                result[child.name] = tags
    return result
