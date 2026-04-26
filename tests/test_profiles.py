"""Tests for envault.profiles module."""

import json
import pytest
from pathlib import Path

from envault.profiles import (
    DEFAULT_PROFILE,
    PROFILE_INDEX_FILE,
    load_index,
    save_index,
    register_profile,
    remove_profile,
    vault_filename_for,
    list_profiles,
    resolve_vault_path,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_index_missing_file_returns_empty(base_dir):
    assert load_index(base_dir) == {}


def test_save_and_load_index_round_trip(base_dir):
    data = {"dev": ".env.dev.vault", "prod": ".env.prod.vault"}
    save_index(base_dir, data)
    assert load_index(base_dir) == data


def test_register_profile_creates_index(base_dir):
    register_profile(base_dir, "dev", ".env.dev.vault")
    index = load_index(base_dir)
    assert index["dev"] == ".env.dev.vault"


def test_register_profile_overwrites_existing(base_dir):
    register_profile(base_dir, "dev", ".env.dev.vault")
    register_profile(base_dir, "dev", ".env.dev.v2.vault")
    assert load_index(base_dir)["dev"] == ".env.dev.v2.vault"


def test_remove_profile_returns_true_when_exists(base_dir):
    register_profile(base_dir, "staging", ".env.staging.vault")
    assert remove_profile(base_dir, "staging") is True
    assert "staging" not in load_index(base_dir)


def test_remove_profile_returns_false_when_missing(base_dir):
    assert remove_profile(base_dir, "nonexistent") is False


def test_vault_filename_for_default():
    assert vault_filename_for(DEFAULT_PROFILE) == ".env.vault"


def test_vault_filename_for_named_profile():
    assert vault_filename_for("prod") == ".env.prod.vault"


def test_list_profiles_sorted(base_dir):
    register_profile(base_dir, "prod", ".env.prod.vault")
    register_profile(base_dir, "dev", ".env.dev.vault")
    register_profile(base_dir, "staging", ".env.staging.vault")
    assert list_profiles(base_dir) == ["dev", "prod", "staging"]


def test_resolve_vault_path_known_profile(base_dir):
    register_profile(base_dir, "dev", ".env.dev.vault")
    result = resolve_vault_path(base_dir, "dev")
    assert result == base_dir / ".env.dev.vault"


def test_resolve_vault_path_unknown_profile_returns_none(base_dir):
    assert resolve_vault_path(base_dir, "ghost") is None
