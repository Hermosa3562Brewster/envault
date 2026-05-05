"""Tests for envault.search and envault.cli_search."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.vault import save_vault
from envault.profiles import register_profile
from envault.search import search_key, search_value, SearchError, SearchResult
from envault.cli_search import search_group

MASTER_KEY = "test-master-key-search"


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_profiles(base_dir: Path) -> None:
    vault_a = base_dir / "profileA.vault"
    save_vault(vault_a, MASTER_KEY, {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"})
    register_profile("profileA", vault_a, base_dir=base_dir)

    vault_b = base_dir / "profileB.vault"
    save_vault(vault_b, MASTER_KEY, {"API_KEY": "xyz", "DB_NAME": "mydb", "TOKEN": "abc999"})
    register_profile("profileB", vault_b, base_dir=base_dir)


def test_search_key_finds_matching_keys(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "DB", base_dir=base_dir)
    assert result.has_matches
    keys = {m.key for m in result.matches}
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "DB_NAME" in keys


def test_search_key_no_matches_returns_empty(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "NONEXISTENT", base_dir=base_dir)
    assert not result.has_matches
    assert result.matches == []


def test_search_key_scoped_to_profile(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "DB", base_dir=base_dir, profile="profileA")
    profiles = {m.profile for m in result.matches}
    assert profiles == {"profileA"}


def test_search_key_case_insensitive_by_default(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "db", base_dir=base_dir)
    assert result.has_matches


def test_search_key_case_sensitive_no_match(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "db", base_dir=base_dir, case_sensitive=True)
    assert not result.has_matches


def test_search_value_finds_matching_values(base_dir: Path, setup_profiles: None) -> None:
    result = search_value(MASTER_KEY, "abc", base_dir=base_dir)
    assert result.has_matches
    keys = {m.key for m in result.matches}
    assert "SECRET" in keys
    assert "TOKEN" in keys


def test_search_value_wrong_key_raises_search_error(base_dir: Path, setup_profiles: None) -> None:
    with pytest.raises(SearchError):
        search_key("wrong-key", "DB", base_dir=base_dir)


def test_by_profile_groups_correctly(base_dir: Path, setup_profiles: None) -> None:
    result = search_key(MASTER_KEY, "DB", base_dir=base_dir)
    grouped = result.by_profile()
    assert "profileA" in grouped
    assert "profileB" in grouped


def test_search_empty_index_returns_empty(base_dir: Path) -> None:
    result = search_key(MASTER_KEY, "anything", base_dir=base_dir)
    assert not result.has_matches


# --- CLI tests ---


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_search_key_prints_matches(runner: CliRunner, base_dir: Path, setup_profiles: None) -> None:
    result = runner.invoke(
        search_group,
        ["key", "DB", "--master-key", MASTER_KEY],
        env={"ENVAULT_BASE_DIR": str(base_dir)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output


def test_cli_search_key_no_matches_message(runner: CliRunner, base_dir: Path, setup_profiles: None) -> None:
    result = runner.invoke(
        search_group,
        ["key", "ZZZNOPE", "--master-key", MASTER_KEY],
        env={"ENVAULT_BASE_DIR": str(base_dir)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_cli_search_value_show_values(runner: CliRunner, base_dir: Path, setup_profiles: None) -> None:
    result = runner.invoke(
        search_group,
        ["value", "abc", "--master-key", MASTER_KEY, "--show-values"],
        env={"ENVAULT_BASE_DIR": str(base_dir)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "=" in result.output
