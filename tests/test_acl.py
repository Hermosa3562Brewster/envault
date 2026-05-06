"""Tests for envault.acl."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.acl import (
    ACLError,
    add_rule,
    filter_env,
    is_allowed,
    load_acl,
    remove_rule,
    save_acl,
)


@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myprofile"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_acl_missing_file_returns_empty(profile_dir):
    acl = load_acl(profile_dir)
    assert acl == {"allow": [], "deny": []}


def test_save_and_load_round_trip(profile_dir):
    original = {"allow": ["DB_*"], "deny": ["SECRET"]}
    save_acl(profile_dir, original)
    assert load_acl(profile_dir) == original


def test_load_corrupt_json_raises_acl_error(profile_dir):
    (profile_dir / "acl.json").write_text("not-json")
    with pytest.raises(ACLError):
        load_acl(profile_dir)


# ---------------------------------------------------------------------------
# add_rule / remove_rule
# ---------------------------------------------------------------------------

def test_add_allow_rule(profile_dir):
    add_rule(profile_dir, "allow", "DB_*")
    assert "DB_*" in load_acl(profile_dir)["allow"]


def test_add_deny_rule(profile_dir):
    add_rule(profile_dir, "deny", "SECRET_KEY")
    assert "SECRET_KEY" in load_acl(profile_dir)["deny"]


def test_add_rule_no_duplicates(profile_dir):
    add_rule(profile_dir, "allow", "DB_*")
    add_rule(profile_dir, "allow", "DB_*")
    assert load_acl(profile_dir)["allow"].count("DB_*") == 1


def test_add_rule_unknown_type_raises(profile_dir):
    with pytest.raises(ACLError, match="Unknown rule type"):
        add_rule(profile_dir, "readwrite", "FOO")


def test_remove_rule_deletes_pattern(profile_dir):
    add_rule(profile_dir, "deny", "PRIVATE_*")
    remove_rule(profile_dir, "deny", "PRIVATE_*")
    assert "PRIVATE_*" not in load_acl(profile_dir)["deny"]


def test_remove_rule_noop_when_absent(profile_dir):
    # Should not raise
    remove_rule(profile_dir, "allow", "NONEXISTENT")


# ---------------------------------------------------------------------------
# is_allowed
# ---------------------------------------------------------------------------

def test_empty_acl_allows_everything():
    acl = {"allow": [], "deny": []}
    assert is_allowed("ANY_KEY", acl) is True


def test_deny_list_blocks_matching_key():
    acl = {"allow": [], "deny": ["SECRET_*"]}
    assert is_allowed("SECRET_TOKEN", acl) is False


def test_deny_list_passes_non_matching_key():
    acl = {"allow": [], "deny": ["SECRET_*"]}
    assert is_allowed("DB_HOST", acl) is True


def test_allow_list_permits_matching_key():
    acl = {"allow": ["DB_*"], "deny": []}
    assert is_allowed("DB_HOST", acl) is True


def test_allow_list_blocks_non_matching_key():
    acl = {"allow": ["DB_*"], "deny": []}
    assert is_allowed("SECRET_KEY", acl) is False


def test_deny_takes_precedence_over_allow():
    acl = {"allow": ["DB_*"], "deny": ["DB_PASSWORD"]}
    assert is_allowed("DB_PASSWORD", acl) is False
    assert is_allowed("DB_HOST", acl) is True


# ---------------------------------------------------------------------------
# filter_env
# ---------------------------------------------------------------------------

def test_filter_env_removes_denied_keys():
    env = {"DB_HOST": "localhost", "SECRET_KEY": "abc", "PORT": "5432"}
    acl = {"allow": [], "deny": ["SECRET_*"]}
    result = filter_env(env, acl)
    assert "SECRET_KEY" not in result
    assert "DB_HOST" in result


def test_filter_env_keeps_only_allowed_keys():
    env = {"DB_HOST": "localhost", "SECRET_KEY": "abc", "PORT": "5432"}
    acl = {"allow": ["DB_*"], "deny": []}
    result = filter_env(env, acl)
    assert result == {"DB_HOST": "localhost"}


def test_filter_env_empty_acl_returns_full_env():
    env = {"A": "1", "B": "2"}
    acl = {"allow": [], "deny": []}
    assert filter_env(env, acl) == env
