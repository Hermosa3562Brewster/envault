"""Integration tests for the sync CLI commands."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_sync import sync_group
from envault.profiles import save_index


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def setup_profile(tmp_path: Path):
    """Create a fake vault file and register it in the index."""
    vault_file = tmp_path / "default.vault"
    vault_file.write_bytes(b"FAKE_VAULT_DATA")
    index = {"default": {"vault_path": str(vault_file), "env_path": str(tmp_path / ".env")}}
    save_index(index)
    return vault_file, tmp_path


def test_push_cmd_succeeds(runner, setup_profile, tmp_path):
    vault_file, _ = setup_profile
    sync_dir = tmp_path / "shared"
    result = runner.invoke(sync_group, ["push", "default", "--sync-dir", str(sync_dir)])
    assert result.exit_code == 0
    assert "Pushed" in result.output
    assert (sync_dir / "default.vault").exists()


def test_push_cmd_unknown_profile_exits_nonzero(runner, tmp_path):
    save_index({})
    result = runner.invoke(sync_group, ["push", "ghost", "--sync-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_pull_cmd_restores_vault(runner, setup_profile, tmp_path):
    vault_file, _ = setup_profile
    sync_dir = tmp_path / "shared"
    # push first
    runner.invoke(sync_group, ["push", "default", "--sync-dir", str(sync_dir)])
    vault_file.unlink()  # remove local copy
    result = runner.invoke(sync_group, ["pull", "default", "--sync-dir", str(sync_dir)])
    assert result.exit_code == 0
    assert vault_file.read_bytes() == b"FAKE_VAULT_DATA"


def test_pull_cmd_with_explicit_vault_path(runner, setup_profile, tmp_path):
    vault_file, _ = setup_profile
    sync_dir = tmp_path / "shared"
    runner.invoke(sync_group, ["push", "default", "--sync-dir", str(sync_dir)])
    out_path = tmp_path / "custom_out.vault"
    result = runner.invoke(
        sync_group,
        ["pull", "default", "--sync-dir", str(sync_dir), "--vault-path", str(out_path)],
    )
    assert result.exit_code == 0
    assert out_path.exists()


def test_status_cmd_lists_vaults(runner, setup_profile, tmp_path):
    vault_file, _ = setup_profile
    sync_dir = tmp_path / "shared"
    runner.invoke(sync_group, ["push", "default", "--sync-dir", str(sync_dir)])
    result = runner.invoke(sync_group, ["status", "--sync-dir", str(sync_dir)])
    assert result.exit_code == 0
    assert "default" in result.output


def test_status_cmd_empty_dir(runner, tmp_path):
    sync_dir = tmp_path / "empty_shared"
    sync_dir.mkdir()
    result = runner.invoke(sync_group, ["status", "--sync-dir", str(sync_dir)])
    assert result.exit_code == 0
    assert "No vaults" in result.output
