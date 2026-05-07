"""Policy enforcement for envault profiles.

Allows defining rules that restrict which keys may be stored or accessed
in a vault profile (e.g. forbidden key patterns, required key presence).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class PolicyError(Exception):
    """Raised when a policy operation fails."""


@dataclass
class PolicyRule:
    kind: str          # 'require' | 'forbid'
    pattern: str       # regex pattern matched against key names
    reason: str = ""


@dataclass
class PolicyResult:
    violations: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def _policy_path(profile_dir: Path) -> Path:
    return profile_dir / "policy.json"


def load_policy(profile_dir: Path) -> List[PolicyRule]:
    """Load policy rules from *profile_dir*. Returns empty list if not set."""
    path = _policy_path(profile_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [PolicyRule(**r) for r in data]
    except Exception as exc:
        raise PolicyError(f"Failed to load policy: {exc}") from exc


def save_policy(profile_dir: Path, rules: List[PolicyRule]) -> None:
    """Persist *rules* to *profile_dir*."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    path = _policy_path(profile_dir)
    try:
        path.write_text(json.dumps([r.__dict__ for r in rules], indent=2))
    except Exception as exc:
        raise PolicyError(f"Failed to save policy: {exc}") from exc


def add_rule(profile_dir: Path, kind: str, pattern: str, reason: str = "") -> None:
    """Append a new rule to the profile policy."""
    if kind not in ("require", "forbid"):
        raise PolicyError(f"Unknown rule kind '{kind}'; expected 'require' or 'forbid'")
    try:
        re.compile(pattern)
    except re.error as exc:
        raise PolicyError(f"Invalid pattern '{pattern}': {exc}") from exc
    rules = load_policy(profile_dir)
    rules.append(PolicyRule(kind=kind, pattern=pattern, reason=reason))
    save_policy(profile_dir, rules)


def remove_rule(profile_dir: Path, pattern: str) -> bool:
    """Remove all rules whose pattern matches *pattern* exactly. Returns True if any removed."""
    rules = load_policy(profile_dir)
    filtered = [r for r in rules if r.pattern != pattern]
    if len(filtered) == len(rules):
        return False
    save_policy(profile_dir, filtered)
    return True


def enforce(env: Dict[str, str], rules: List[PolicyRule]) -> PolicyResult:
    """Check *env* against *rules* and return a PolicyResult."""
    result = PolicyResult()
    for rule in rules:
        try:
            rx = re.compile(rule.pattern)
        except re.error:
            continue
        if rule.kind == "forbid":
            for key in env:
                if rx.search(key):
                    msg = f"Key '{key}' is forbidden by pattern '{rule.pattern}'"
                    if rule.reason:
                        msg += f" ({rule.reason})"
                    result.violations.append(msg)
        elif rule.kind == "require":
            if not any(rx.search(k) for k in env):
                msg = f"No key matching '{rule.pattern}' found (required)"
                if rule.reason:
                    msg += f" ({rule.reason})"
                result.violations.append(msg)
    return result
