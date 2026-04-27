"""Tests for envault.diff module."""

import pytest

from envault.diff import EnvDiff, diff_envs


# ---------------------------------------------------------------------------
# diff_envs
# ---------------------------------------------------------------------------

def test_identical_envs_produce_no_changes():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = diff_envs(env, env.copy())
    assert not result.has_changes


def test_added_keys_detected():
    old = {"FOO": "1"}
    new = {"FOO": "1", "BAR": "2"}
    result = diff_envs(old, new)
    assert result.added == {"BAR": "2"}
    assert not result.removed
    assert not result.changed


def test_removed_keys_detected():
    old = {"FOO": "1", "BAR": "2"}
    new = {"FOO": "1"}
    result = diff_envs(old, new)
    assert result.removed == {"BAR": "2"}
    assert not result.added
    assert not result.changed


def test_changed_values_detected():
    old = {"FOO": "old_value"}
    new = {"FOO": "new_value"}
    result = diff_envs(old, new)
    assert result.changed == {"FOO": ("old_value", "new_value")}
    assert not result.added
    assert not result.removed


def test_combined_diff():
    old = {"KEEP": "same", "MODIFY": "v1", "DROP": "gone"}
    new = {"KEEP": "same", "MODIFY": "v2", "NEW": "hello"}
    result = diff_envs(old, new)
    assert result.added == {"NEW": "hello"}
    assert result.removed == {"DROP": "gone"}
    assert result.changed == {"MODIFY": ("v1", "v2")}
    assert result.has_changes


def test_empty_old_and_new():
    result = diff_envs({}, {})
    assert not result.has_changes


def test_empty_old_all_added():
    new = {"A": "1", "B": "2"}
    result = diff_envs({}, new)
    assert result.added == new
    assert not result.removed
    assert not result.changed


# ---------------------------------------------------------------------------
# EnvDiff.summary_lines
# ---------------------------------------------------------------------------

def test_summary_lines_format():
    diff = EnvDiff(
        added={"NEW_KEY": "val"},
        removed={"OLD_KEY": "gone"},
        changed={"MOD_KEY": ("before", "after")},
    )
    lines = diff.summary_lines()
    assert any(line.startswith("  +") and "NEW_KEY" in line for line in lines)
    assert any(line.startswith("  -") and "OLD_KEY" in line for line in lines)
    assert any(line.startswith("  ~") and "MOD_KEY" in line for line in lines)


def test_summary_lines_empty_when_no_changes():
    diff = EnvDiff()
    assert diff.summary_lines() == []
