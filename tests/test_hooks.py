"""Tests for envault.hooks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from envault.hooks import (
    HookError,
    VALID_EVENTS,
    load_hooks,
    remove_hook,
    run_hooks,
    save_hooks,
    set_hook,
)


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    return tmp_path / "myprofile"


def test_load_hooks_missing_file_returns_empty(profile_dir):
    assert load_hooks(profile_dir) == {}


def test_save_and_load_round_trip(profile_dir):
    hooks = {"post_lock": ["echo locked"]}
    save_hooks(profile_dir, hooks)
    assert load_hooks(profile_dir) == hooks


def test_set_hook_creates_file(profile_dir):
    set_hook(profile_dir, "post_unlock", "echo done")
    hooks = load_hooks(profile_dir)
    assert "post_unlock" in hooks
    assert hooks["post_unlock"] == ["echo done"]


def test_set_hook_appends_multiple_commands(profile_dir):
    set_hook(profile_dir, "pre_lock", "echo first")
    set_hook(profile_dir, "pre_lock", "echo second")
    hooks = load_hooks(profile_dir)
    assert hooks["pre_lock"] == ["echo first", "echo second"]


def test_set_hook_invalid_event_raises(profile_dir):
    with pytest.raises(ValueError, match="Unknown event"):
        set_hook(profile_dir, "on_explode", "rm -rf /")


def test_remove_hook_removes_correct_index(profile_dir):
    set_hook(profile_dir, "post_lock", "echo a")
    set_hook(profile_dir, "post_lock", "echo b")
    remove_hook(profile_dir, "post_lock", 0)
    assert load_hooks(profile_dir)["post_lock"] == ["echo b"]


def test_remove_hook_cleans_up_empty_event(profile_dir):
    set_hook(profile_dir, "post_lock", "echo a")
    remove_hook(profile_dir, "post_lock", 0)
    assert "post_lock" not in load_hooks(profile_dir)


def test_remove_hook_bad_index_raises(profile_dir):
    set_hook(profile_dir, "post_lock", "echo a")
    with pytest.raises(IndexError):
        remove_hook(profile_dir, "post_lock", 5)


def test_run_hooks_executes_command(profile_dir, tmp_path):
    sentinel = tmp_path / "ran.txt"
    set_hook(profile_dir, "post_unlock", f"touch {sentinel}")
    run_hooks(profile_dir, "post_unlock")
    assert sentinel.exists()


def test_run_hooks_no_hooks_is_noop(profile_dir):
    # Should not raise even with no hooks registered
    run_hooks(profile_dir, "pre_lock")


def test_run_hooks_failing_command_raises_hook_error(profile_dir):
    set_hook(profile_dir, "pre_rotate", f"{sys.executable} -c 'raise SystemExit(1)'")
    with pytest.raises(HookError, match="pre_rotate"):
        run_hooks(profile_dir, "pre_rotate")


def test_valid_events_set_is_complete():
    expected = {
        "pre_lock", "post_lock",
        "pre_unlock", "post_unlock",
        "pre_rotate", "post_rotate",
    }
    assert VALID_EVENTS == expected
