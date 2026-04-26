"""Tests for the envault CLI (envault.cli)."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli

MASTER_KEY = "super-secret-test-key-1234"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV, encoding="utf-8")
    return p


def test_lock_creates_vault_file(runner, env_file, tmp_path):
    vault_path = tmp_path / ".env.vault"
    result = runner.invoke(
        cli,
        ["lock", str(env_file), "--output", str(vault_path), "--key", MASTER_KEY],
    )
    assert result.exit_code == 0, result.output
    assert vault_path.exists()
    assert "Locked" in result.output


def test_unlock_restores_env(runner, env_file, tmp_path):
    vault_path = tmp_path / ".env.vault"
    out_path = tmp_path / ".env.decrypted"

    runner.invoke(
        cli,
        ["lock", str(env_file), "--output", str(vault_path), "--key", MASTER_KEY],
    )
    result = runner.invoke(
        cli,
        ["unlock", str(vault_path), "--output", str(out_path), "--key", MASTER_KEY],
    )
    assert result.exit_code == 0, result.output
    assert out_path.read_text(encoding="utf-8") == SAMPLE_ENV


def test_unlock_wrong_key_exits_nonzero(runner, env_file, tmp_path):
    vault_path = tmp_path / ".env.vault"
    runner.invoke(
        cli,
        ["lock", str(env_file), "--output", str(vault_path), "--key", MASTER_KEY],
    )
    result = runner.invoke(
        cli,
        ["unlock", str(vault_path), "--output", str(tmp_path / "out"), "--key", "wrong-key"],
    )
    assert result.exit_code != 0


def test_view_prints_secrets(runner, env_file, tmp_path):
    vault_path = tmp_path / ".env.vault"
    runner.invoke(
        cli,
        ["lock", str(env_file), "--output", str(vault_path), "--key", MASTER_KEY],
    )
    result = runner.invoke(cli, ["view", str(vault_path), "--key", MASTER_KEY])
    assert result.exit_code == 0
    assert "DB_HOST=localhost" in result.output


def test_view_wrong_key_exits_nonzero(runner, env_file, tmp_path):
    vault_path = tmp_path / ".env.vault"
    runner.invoke(
        cli,
        ["lock", str(env_file), "--output", str(vault_path), "--key", MASTER_KEY],
    )
    result = runner.invoke(cli, ["view", str(vault_path), "--key", "bad-key"])
    assert result.exit_code != 0
