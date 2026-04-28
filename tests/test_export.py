"""Tests for envault.export and the export CLI command."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from envault.export import ExportError, export_dotenv, export_env, export_json, export_shell


# ---------------------------------------------------------------------------
# Unit tests for pure export helpers
# ---------------------------------------------------------------------------

ENV = {"DB_HOST": "localhost", "SECRET": "p@ss w0rd!", "PORT": "5432"}


def test_export_dotenv_contains_all_keys():
    out = export_dotenv(ENV)
    for key in ENV:
        assert key in out


def test_export_dotenv_quotes_values_with_spaces():
    out = export_dotenv({"MSG": "hello world"})
    assert "'hello world'" in out or '"hello world"' in out or "hello\\ world" in out


def test_export_dotenv_simple_value_unquoted():
    out = export_dotenv({"PORT": "5432"})
    assert "PORT=5432" in out


def test_export_shell_uses_export_keyword():
    out = export_shell(ENV)
    for key in ENV:
        assert f"export {key}=" in out


def test_export_json_is_valid_json():
    out = export_json(ENV)
    parsed = json.loads(out)
    assert parsed == ENV


def test_export_json_keys_sorted():
    out = export_json(ENV)
    parsed = json.loads(out)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_export_env_dispatches_dotenv():
    out = export_env(ENV, "dotenv")
    assert "DB_HOST=" in out


def test_export_env_dispatches_shell():
    out = export_env(ENV, "shell")
    assert "export PORT=" in out


def test_export_env_dispatches_json():
    out = export_env(ENV, "json")
    assert json.loads(out)["PORT"] == "5432"


def test_export_env_unknown_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_env(ENV, "yaml")


def test_export_empty_env_produces_empty_output():
    assert export_dotenv({}) == ""
    assert export_shell({}) == ""
    assert json.loads(export_json({})) == {}


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def setup_profile(tmp_path, monkeypatch):
    """Create a locked vault and register it as a profile named 'myapp'."""
    from envault.vault import save_vault
    from envault.profiles import register_profile

    vault_path = tmp_path / "myapp.vault"
    save_vault({"APP_ENV": "production", "TOKEN": "abc123"}, str(vault_path), "masterkey")
    register_profile("myapp", str(vault_path), base_dir=str(tmp_path))
    monkeypatch.setenv("ENVAULT_PROFILES_DIR", str(tmp_path))
    return vault_path


def test_export_cmd_stdout_dotenv(runner, setup_profile):
    from envault.cli_export import export_cmd

    result = runner.invoke(export_cmd, ["myapp", "--key", "masterkey", "--format", "dotenv"])
    assert result.exit_code == 0
    assert "APP_ENV=" in result.output


def test_export_cmd_stdout_json(runner, setup_profile):
    from envault.cli_export import export_cmd

    result = runner.invoke(export_cmd, ["myapp", "--key", "masterkey", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["TOKEN"] == "abc123"


def test_export_cmd_wrong_key_exits_nonzero(runner, setup_profile):
    from envault.cli_export import export_cmd

    result = runner.invoke(export_cmd, ["myapp", "--key", "wrongkey", "--format", "dotenv"])
    assert result.exit_code != 0


def test_export_cmd_unknown_profile_exits_nonzero(runner, tmp_path, monkeypatch):
    from envault.cli_export import export_cmd

    monkeypatch.setenv("ENVAULT_PROFILES_DIR", str(tmp_path))
    result = runner.invoke(export_cmd, ["ghost", "--key", "k", "--format", "dotenv"])
    assert result.exit_code != 0
