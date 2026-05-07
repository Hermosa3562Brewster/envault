"""Tests for envault.policy."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.policy import (
    PolicyError,
    PolicyRule,
    add_rule,
    enforce,
    load_policy,
    remove_rule,
    save_policy,
)


@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myprofile"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_policy_missing_file_returns_empty(profile_dir):
    assert load_policy(profile_dir) == []


def test_save_and_load_round_trip(profile_dir):
    rules = [
        PolicyRule(kind="require", pattern="^DB_", reason="database creds required"),
        PolicyRule(kind="forbid", pattern="SECRET"),
    ]
    save_policy(profile_dir, rules)
    loaded = load_policy(profile_dir)
    assert len(loaded) == 2
    assert loaded[0].kind == "require"
    assert loaded[0].pattern == "^DB_"
    assert loaded[1].kind == "forbid"


def test_load_corrupt_json_raises_policy_error(profile_dir):
    (profile_dir / "policy.json").write_text("not json{{")
    with pytest.raises(PolicyError):
        load_policy(profile_dir)


# ---------------------------------------------------------------------------
# add_rule
# ---------------------------------------------------------------------------

def test_add_rule_creates_file(profile_dir):
    add_rule(profile_dir, "forbid", "^PRIVATE_")
    rules = load_policy(profile_dir)
    assert len(rules) == 1
    assert rules[0].kind == "forbid"


def test_add_rule_appends(profile_dir):
    add_rule(profile_dir, "require", "^APP_")
    add_rule(profile_dir, "forbid", "^DEBUG")
    assert len(load_policy(profile_dir)) == 2


def test_add_rule_invalid_kind_raises(profile_dir):
    with pytest.raises(PolicyError, match="Unknown rule kind"):
        add_rule(profile_dir, "deny", ".*")


def test_add_rule_invalid_pattern_raises(profile_dir):
    with pytest.raises(PolicyError, match="Invalid pattern"):
        add_rule(profile_dir, "forbid", "[unclosed")


# ---------------------------------------------------------------------------
# remove_rule
# ---------------------------------------------------------------------------

def test_remove_rule_returns_true_when_found(profile_dir):
    add_rule(profile_dir, "forbid", "^PRIVATE_")
    assert remove_rule(profile_dir, "^PRIVATE_") is True
    assert load_policy(profile_dir) == []


def test_remove_rule_returns_false_when_not_found(profile_dir):
    assert remove_rule(profile_dir, "nonexistent") is False


# ---------------------------------------------------------------------------
# enforce
# ---------------------------------------------------------------------------

def test_enforce_no_rules_passes():
    result = enforce({"DB_HOST": "localhost"}, [])
    assert result.passed


def test_enforce_require_passes_when_key_present():
    rules = [PolicyRule(kind="require", pattern="^DB_")]
    result = enforce({"DB_HOST": "localhost", "APP_ENV": "prod"}, rules)
    assert result.passed


def test_enforce_require_fails_when_key_absent():
    rules = [PolicyRule(kind="require", pattern="^DB_", reason="need db")]
    result = enforce({"APP_ENV": "prod"}, rules)
    assert not result.passed
    assert any("required" in v for v in result.violations)


def test_enforce_forbid_passes_when_key_absent():
    rules = [PolicyRule(kind="forbid", pattern="^SECRET")]
    result = enforce({"DB_HOST": "localhost"}, rules)
    assert result.passed


def test_enforce_forbid_fails_when_key_present():
    rules = [PolicyRule(kind="forbid", pattern="^SECRET", reason="no secrets allowed")]
    result = enforce({"SECRET_KEY": "abc123", "DB_HOST": "x"}, rules)
    assert not result.passed
    assert any("SECRET_KEY" in v for v in result.violations)


def test_enforce_multiple_violations_reported():
    rules = [
        PolicyRule(kind="require", pattern="^DB_"),
        PolicyRule(kind="forbid", pattern="DEBUG"),
    ]
    env = {"DEBUG_MODE": "true"}  # missing DB_ AND has DEBUG key
    result = enforce(env, rules)
    assert not result.passed
    assert len(result.violations) == 2
