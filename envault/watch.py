"""Watch a .env file for changes and auto-lock into the vault."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when the file watcher encounters a fatal error."""


def _mtime(path: Path) -> Optional[float]:
    """Return the modification time of *path*, or None if it does not exist."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return None


def watch(
    env_path: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *env_path* every *interval* seconds and call *on_change* when it
    is modified.

    Parameters
    ----------
    env_path:
        Path to the ``.env`` file to monitor.
    on_change:
        Callable invoked with *env_path* whenever a change is detected.
    interval:
        Polling interval in seconds (default 1.0).
    max_iterations:
        If given, stop after this many poll cycles (useful for testing).

    Raises
    ------
    WatchError
        If *env_path*'s parent directory does not exist.
    """
    env_path = Path(env_path)
    if not env_path.parent.exists():
        raise WatchError(f"Directory does not exist: {env_path.parent}")

    last_mtime = _mtime(env_path)
    iterations = 0

    while True:
        time.sleep(interval)
        current_mtime = _mtime(env_path)

        if current_mtime is not None and current_mtime != last_mtime:
            last_mtime = current_mtime
            on_change(env_path)

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
