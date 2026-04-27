"""Utilities for diffing .env files to detect added, removed, or changed keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class EnvDiff:
    """Result of comparing two sets of env variables."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary_lines(self) -> List[str]:
        """Return human-readable summary lines for display."""
        lines: List[str] = []
        for key in sorted(self.added):
            lines.append(f"  + {key}={self.added[key]}")
        for key in sorted(self.removed):
            lines.append(f"  - {key}={self.removed[key]}")
        for key in sorted(self.changed):
            old, new = self.changed[key]
            lines.append(f"  ~ {key}: {old!r} -> {new!r}")
        return lines


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
) -> EnvDiff:
    """Compare two env dicts and return an EnvDiff describing the differences.

    Args:
        old: The baseline env mapping (e.g. currently unlocked values).
        new: The updated env mapping (e.g. freshly loaded from vault).

    Returns:
        An :class:`EnvDiff` instance describing what changed.
    """
    old_keys = set(old)
    new_keys = set(new)

    added = {k: new[k] for k in new_keys - old_keys}
    removed = {k: old[k] for k in old_keys - new_keys}
    changed = {
        k: (old[k], new[k])
        for k in old_keys & new_keys
        if old[k] != new[k]
    }

    return EnvDiff(added=added, removed=removed, changed=changed)
