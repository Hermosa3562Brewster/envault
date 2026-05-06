"""Tests for envault.cli_quota."""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_quota import quota_group
from envault.quota import DEFAULT_QUOTA, load_quota, set_limit


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def setup_profile(tmp_path: Path, monkeypatch):
    """Create a minimal profile and patch load_index to return it."""
    vault_file = tmp_path / "myprofile" / "secrets.vault"
    vault_file.parent.mkdir(parents=True)
    vault_file.touch()

    index = {"myprofile": {"path": str(vault_file)}}

    monkeypatch.setattr("envault.cli_quota.load_index", lambda: index)
    return tmp_path / "myprofile"


def test_set_cmd_global_limit(runner, setup_profile):
    result = runner.invoke(quota_group, ["set", "myprofile", "30"])
    assert result.exit_code == 0
    assert "30" in result.output
    record = load_quota(setup_profile)
    assert record.limit == 30


def test_set_cmd_per_key_limit(runner, setup_profile):
    result = runner.invoke(quota_group, ["set", "myprofile", "5", "--key", "DB_PASS"])
    assert result.exit_code == 0
    record = load_quota(setup_profile)
    assert record.overrides["DB_PASS"] == 5


def test_set_cmd_invalid_limit_exits_nonzero(runner, setup_profile):
    result = runner.invoke(quota_group, ["set", "myprofile", "0"])
    assert result.exit_code != 0


def test_set_cmd_unknown_profile_exits_nonzero(runner, setup_profile):
    result = runner.invoke(quota_group, ["set", "unknown", "10"])
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_show_cmd_displays_defaults(runner, setup_profile):
    result = runner.invoke(quota_group, ["show", "myprofile"])
    assert result.exit_code == 0
    assert str(DEFAULT_QUOTA) in result.output
    assert "No per-key overrides" in result.output


def test_show_cmd_displays_overrides(runner, setup_profile):
    set_limit(setup_profile, 7, key="SECRET")
    result = runner.invoke(quota_group, ["show", "myprofile"])
    assert result.exit_code == 0
    assert "SECRET" in result.output
    assert "7" in result.output


def test_remove_override_cmd_succeeds(runner, setup_profile):
    set_limit(setup_profile, 3, key="TOKEN")
    result = runner.invoke(quota_group, ["remove-override", "myprofile", "TOKEN"])
    assert result.exit_code == 0
    assert "TOKEN" in result.output
    record = load_quota(setup_profile)
    assert "TOKEN" not in record.overrides


def test_remove_override_cmd_missing_key_exits_nonzero(runner, setup_profile):
    result = runner.invoke(quota_group, ["remove-override", "myprofile", "GHOST"])
    assert result.exit_code != 0
    assert "No override found" in result.output
