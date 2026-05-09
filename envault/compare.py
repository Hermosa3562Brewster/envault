"""Compare two vault profiles or snapshots side-by-side."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import load_vault
from envault.profiles import get_profile


class CompareError(Exception):
    """Raised when a comparison cannot be completed."""


@dataclass
class CompareResult:
    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)   # key -> (left_val, right_val)
    identical: Dict[str, str] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.changed)


def compare_vaults(left_path: Path, right_path: Path, master_key: str) -> CompareResult:
    """Decrypt and compare two vault files using the same master key."""
    if not left_path.exists():
        raise CompareError(f"Left vault not found: {left_path}")
    if not right_path.exists():
        raise CompareError(f"Right vault not found: {right_path}")

    left_env = load_vault(left_path, master_key)
    right_env = load_vault(right_path, master_key)
    return _compare_dicts(left_env, right_env)


def compare_profiles(
    left_profile: str,
    right_profile: str,
    master_key: str,
    base_dir: Optional[Path] = None,
) -> CompareResult:
    """Compare two named profiles by resolving their vault paths."""
    left_meta = get_profile(left_profile, base_dir=base_dir)
    right_meta = get_profile(right_profile, base_dir=base_dir)
    if left_meta is None:
        raise CompareError(f"Unknown profile: {left_profile}")
    if right_meta is None:
        raise CompareError(f"Unknown profile: {right_profile}")
    return compare_vaults(Path(left_meta["vault"]), Path(right_meta["vault"]), master_key)


def _compare_dicts(left: Dict[str, str], right: Dict[str, str]) -> CompareResult:
    result = CompareResult()
    all_keys = set(left) | set(right)
    for key in sorted(all_keys):
        in_left = key in left
        in_right = key in right
        if in_left and not in_right:
            result.only_in_left[key] = left[key]
        elif in_right and not in_left:
            result.only_in_right[key] = right[key]
        elif left[key] != right[key]:
            result.changed[key] = (left[key], right[key])
        else:
            result.identical[key] = left[key]
    return result


def summary_lines(result: CompareResult, left_label: str = "left", right_label: str = "right") -> List[str]:
    """Return human-readable summary lines for a CompareResult."""
    lines: List[str] = []
    for key, val in result.only_in_left.items():
        lines.append(f"  < {key}={val}  (only in {left_label})")
    for key, val in result.only_in_right.items():
        lines.append(f"  > {key}={val}  (only in {right_label})")
    for key, (lv, rv) in result.changed.items():
        lines.append(f"  ~ {key}: {lv!r} -> {rv!r}")
    if not result.has_differences:
        lines.append(f"  (no differences between {left_label} and {right_label})")
    return lines


def stats(result: CompareResult) -> Dict[str, int]:
    """Return a dictionary of counts for each category in the comparison result.

    Useful for quick programmatic inspection or displaying a summary header.
    """
    return {
        "only_in_left": len(result.only_in_left),
        "only_in_right": len(result.only_in_right),
        "changed": len(result.changed),
        "identical": len(result.identical),
        "total": len(result.only_in_left) + len(result.only_in_right)
                 + len(result.changed) + len(result.identical),
    }
