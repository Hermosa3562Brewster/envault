"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.watch import WatchError, _mtime, watch


# ---------------------------------------------------------------------------
# _mtime helpers
# ---------------------------------------------------------------------------

def test_mtime_returns_float_for_existing_file(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=val")
    result = _mtime(f)
    assert isinstance(result, float)


def test_mtime_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _mtime(tmp_path / "nonexistent.env") is None


# ---------------------------------------------------------------------------
# watch – error cases
# ---------------------------------------------------------------------------

def test_watch_raises_if_parent_dir_missing(tmp_path: Path) -> None:
    missing_dir = tmp_path / "ghost"
    with pytest.raises(WatchError, match="Directory does not exist"):
        watch(missing_dir / ".env", on_change=MagicMock(), max_iterations=1)


# ---------------------------------------------------------------------------
# watch – change detection
# ---------------------------------------------------------------------------

def test_watch_calls_on_change_when_file_modified(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("A=1")

    callback = MagicMock()
    call_count = 0

    original_mtime = _mtime(env_file)

    def fake_sleep(interval: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Simulate a write by bumping the mtime via os.utime
            new_time = original_mtime + 10.0  # type: ignore[operator]
            import os
            os.utime(env_file, (new_time, new_time))

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch(env_file, on_change=callback, interval=0.0, max_iterations=2)

    callback.assert_called_once_with(env_file)


def test_watch_does_not_call_on_change_when_file_unchanged(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("A=1")

    callback = MagicMock()

    with patch("envault.watch.time.sleep"):
        watch(env_file, on_change=callback, interval=0.0, max_iterations=3)

    callback.assert_not_called()


def test_watch_ignores_missing_file_without_raising(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    # File does not exist yet – should not raise
    callback = MagicMock()

    with patch("envault.watch.time.sleep"):
        watch(env_file, on_change=callback, interval=0.0, max_iterations=2)

    callback.assert_not_called()
