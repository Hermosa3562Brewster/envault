"""Pre/post hooks for vault operations (lock, unlock, rotate).

Hooks are shell commands stored per-profile in a hooks.json file.
Supported events: pre_lock, post_lock, pre_unlock, post_unlock, pre_rotate, post_rotate
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

VALID_EVENTS = {
    "pre_lock",
    "post_lock",
    "pre_unlock",
    "post_unlock",
    "pre_rotate",
    "post_rotate",
}


class HookError(Exception):
    """Raised when a hook command exits with a non-zero status."""


def _hooks_path(profile_dir: Path) -> Path:
    return profile_dir / "hooks.json"


def load_hooks(profile_dir: Path) -> Dict[str, List[str]]:
    """Return the hooks mapping for *profile_dir*, or an empty dict."""
    path = _hooks_path(profile_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_hooks(profile_dir: Path, hooks: Dict[str, List[str]]) -> None:
    """Persist *hooks* to *profile_dir*/hooks.json."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    with _hooks_path(profile_dir).open("w") as fh:
        json.dump(hooks, fh, indent=2)


def set_hook(profile_dir: Path, event: str, command: str) -> None:
    """Register *command* for *event*, appending if commands already exist."""
    if event not in VALID_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}")
    hooks = load_hooks(profile_dir)
    hooks.setdefault(event, []).append(command)
    save_hooks(profile_dir, hooks)


def remove_hook(profile_dir: Path, event: str, index: int) -> None:
    """Remove the hook at *index* for *event*."""
    hooks = load_hooks(profile_dir)
    commands = hooks.get(event, [])
    if index < 0 or index >= len(commands):
        raise IndexError(f"No hook at index {index} for event '{event}'")
    commands.pop(index)
    if not commands:
        hooks.pop(event, None)
    save_hooks(profile_dir, hooks)


def run_hooks(
    profile_dir: Path,
    event: str,
    extra_env: Optional[Dict[str, str]] = None,
) -> None:
    """Execute all commands registered for *event*.

    Raises HookError if any command exits non-zero.
    """
    hooks = load_hooks(profile_dir)
    commands = hooks.get(event, [])
    import os
    env = {**os.environ, **(extra_env or {})}
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, env=env)
        if result.returncode != 0:
            raise HookError(
                f"Hook for '{event}' failed (exit {result.returncode}): {cmd}"
            )
