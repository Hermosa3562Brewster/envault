"""CLI integration tests, including multi-profile scenarios."""

from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("SECRET=hello\nTOKEN=abc123\n")
    return p


def test_lock_creates_vault_file(runner, env_file, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        env_file.rename(tmp_path / ".env")
        result = runner.invoke(cli, ["lock", ".env", "-p", "mypassword"])
        assert result.exit_code == 0
        assert Path(".env.vault").exists()
        assert "Locked" in result.output


def test_unlock_restores_env(runner, env_file, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        env_file.rename(tmp_path / ".env")
        runner.invoke(cli, ["lock", ".env", "-p", "mypassword"])
        result = runner.invoke(cli, ["unlock", "-p", "mypassword"])
        assert result.exit_code == 0
        assert Path(".env").read_text().strip() != ""


def test_unlock_wrong_key_exits_nonzero(runner, env_file, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        env_file.rename(tmp_path / ".env")
        runner.invoke(cli, ["lock", ".env", "-p", "correct"])
        result = runner.invoke(cli, ["unlock", "-p", "wrong"])
        assert result.exit_code != 0


def test_view_prints_secrets(runner, env_file, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        env_file.rename(tmp_path / ".env")
        runner.invoke(cli, ["lock", ".env", "-p", "pass"])
        result = runner.invoke(cli, ["view", "-p", "pass"])
        assert result.exit_code == 0
        assert "SECRET=hello" in result.output
        assert "TOKEN=abc123" in result.output


def test_lock_and_unlock_named_profile(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".env.staging").write_text("DB=postgres://staging\n")
        result = runner.invoke(cli, ["lock", ".env.staging", "-p", "stagingpass", "--profile", "staging"])
        assert result.exit_code == 0
        assert Path(".env.staging.vault").exists()

        result = runner.invoke(cli, ["unlock", "-p", "stagingpass", "--profile", "staging"])
        assert result.exit_code == 0
        assert "staging" in result.output


def test_profiles_cmd_lists_registered(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".env").write_text("A=1\n")
        runner.invoke(cli, ["lock", ".env", "-p", "x"])
        result = runner.invoke(cli, ["profiles"])
        assert result.exit_code == 0
        assert "default" in result.output


def test_unlock_missing_profile_exits_nonzero(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["unlock", "-p", "any", "--profile", "ghost"])
        assert result.exit_code != 0
