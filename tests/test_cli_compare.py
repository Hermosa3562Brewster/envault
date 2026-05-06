"""Tests for envault.cli_compare CLI commands."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import save_vault
from envault.profiles import register_profile
from envault.cli_compare import compare_group

MASTER_KEY = "cli-compare-test-key"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_pair(tmp_path):
    left = tmp_path / "left.vault"
    right = tmp_path / "right.vault"
    save_vault(left, {"A": "1", "B": "same"}, MASTER_KEY)
    save_vault(right, {"A": "2", "B": "same", "C": "new"}, MASTER_KEY)
    return left, right


def test_compare_files_identical_exits_zero(runner, tmp_path):
    env = {"X": "1", "Y": "2"}
    left = tmp_path / "l.vault"
    right = tmp_path / "r.vault"
    save_vault(left, env, MASTER_KEY)
    save_vault(right, env, MASTER_KEY)
    result = runner.invoke(
        compare_group, ["files", str(left), str(right), "--key", MASTER_KEY]
    )
    assert result.exit_code == 0
    assert "no differences" in result.output


def test_compare_files_with_diffs_exits_nonzero(runner, vault_pair):
    left, right = vault_pair
    result = runner.invoke(
        compare_group, ["files", str(left), str(right), "--key", MASTER_KEY]
    )
    assert result.exit_code != 0
    assert "A" in result.output


def test_compare_files_shows_custom_labels(runner, vault_pair):
    left, right = vault_pair
    result = runner.invoke(
        compare_group,
        ["files", str(left), str(right), "--key", MASTER_KEY,
         "--left-label", "staging", "--right-label", "prod"],
    )
    assert "staging" in result.output or "prod" in result.output


def test_compare_profiles_identical_exits_zero(runner, tmp_path):
    env = {"DB": "localhost"}
    v1 = tmp_path / "p1.vault"
    v2 = tmp_path / "p2.vault"
    save_vault(v1, env, MASTER_KEY)
    save_vault(v2, env, MASTER_KEY)
    register_profile("alpha", str(v1), base_dir=tmp_path)
    register_profile("beta", str(v2), base_dir=tmp_path)
    result = runner.invoke(
        compare_group,
        ["profiles", "alpha", "beta", "--key", MASTER_KEY, "--base-dir", str(tmp_path)],
    )
    assert result.exit_code == 0


def test_compare_profiles_unknown_profile_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        compare_group,
        ["profiles", "ghost", "phantom", "--key", MASTER_KEY, "--base-dir", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "Error" in result.output or "Unknown" in result.output
