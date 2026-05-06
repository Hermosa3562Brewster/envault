"""Access control lists — restrict which keys a profile can read/write."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.profiles import _index_path  # reuse profiles base dir logic


class ACLError(Exception):
    """Raised when an ACL operation fails."""


def _acl_path(profile_dir: Path) -> Path:
    return profile_dir / "acl.json"


def load_acl(profile_dir: Path) -> Dict[str, List[str]]:
    """Return the ACL dict mapping rule names to key patterns.

    Keys in the returned dict:
      ``allow``  – explicit allow-list of key globs (empty == allow all)
      ``deny``   – explicit deny-list of key globs (empty == deny none)
    """
    path = _acl_path(profile_dir)
    if not path.exists():
        return {"allow": [], "deny": []}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ACLError(f"Cannot read ACL file {path}: {exc}") from exc
    return {
        "allow": list(data.get("allow", [])),
        "deny": list(data.get("deny", [])),
    }


def save_acl(profile_dir: Path, acl: Dict[str, List[str]]) -> None:
    """Persist *acl* to *profile_dir*/acl.json."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    _acl_path(profile_dir).write_text(json.dumps(acl, indent=2))


def add_rule(profile_dir: Path, rule: str, pattern: str) -> None:
    """Append *pattern* to the ``allow`` or ``deny`` list in the ACL."""
    if rule not in ("allow", "deny"):
        raise ACLError(f"Unknown rule type '{rule}'; expected 'allow' or 'deny'")
    acl = load_acl(profile_dir)
    if pattern not in acl[rule]:
        acl[rule].append(pattern)
    save_acl(profile_dir, acl)


def remove_rule(profile_dir: Path, rule: str, pattern: str) -> None:
    """Remove *pattern* from the given *rule* list; no-op if absent."""
    if rule not in ("allow", "deny"):
        raise ACLError(f"Unknown rule type '{rule}'; expected 'allow' or 'deny'")
    acl = load_acl(profile_dir)
    acl[rule] = [p for p in acl[rule] if p != pattern]
    save_acl(profile_dir, acl)


def is_allowed(key: str, acl: Dict[str, List[str]]) -> bool:
    """Return True when *key* passes the ACL rules.

    Logic:
    1. If the deny list is non-empty and *key* matches any pattern → denied.
    2. If the allow list is non-empty, *key* must match at least one pattern.
    3. Otherwise allowed.
    """
    import fnmatch

    for pattern in acl.get("deny", []):
        if fnmatch.fnmatch(key, pattern):
            return False
    allow_list = acl.get("allow", [])
    if allow_list:
        return any(fnmatch.fnmatch(key, p) for p in allow_list)
    return True


def filter_env(
    env: Dict[str, str], acl: Dict[str, List[str]]
) -> Dict[str, str]:
    """Return a filtered copy of *env* containing only keys permitted by *acl*."""
    return {k: v for k, v in env.items() if is_allowed(k, acl)}
