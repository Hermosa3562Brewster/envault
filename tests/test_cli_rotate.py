"""Tests for the rotate CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_rotate import rotate_group
from envault.profiles import register_profile
from envault.vault import load_vault, save_vault


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def setup_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Register a profile backed by a real vault file."""
    index_path = tmp_path / "index.json"
    monkeypatch.setattr("envault.profiles._index_path", lambda: index_path)
    monkeypatch.setattr("envault.cli_rotate.load_index", lambda: _load(index_path))

    vault_path = tmp_path / "test.vault"
    save_vault({"KEY": "value", "DB": "postgres"}, vault_path, "old-pass")
    register_profile("myapp", vault_path)
    return vault_path


def _load(path: Path):
    import json
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def test_rotate_key_cmd_succeeds(runner: CliRunner, setup_profile: Path) -> None:
    result = runner.invoke(
        rotate_group,
        ["key", "myapp", "--old-key", "old-pass", "--new-key", "new-pass"],
    )
    assert result.exit_code == 0, result.output
    assert "rotated successfully" in result.output
    env = load_vault(setup_profile, "new-pass")
    assert env["KEY"] == "value"


def test_rotate_key_cmd_wrong_old_key_exits_nonzero(
    runner: CliRunner, setup_profile: Path
) -> None:
    result = runner.invoke(
        rotate_group,
        ["key", "myapp", "--old-key", "wrong", "--new-key", "new-pass"],
    )
    assert result.exit_code != 0
    assert "incorrect" in result.output.lower() or "Error" in result.output


def test_rotate_key_cmd_unknown_profile_exits_nonzero(runner: CliRunner, setup_profile: Path) -> None:
    result = runner.invoke(
        rotate_group,
        ["key", "ghost", "--old-key", "old-pass", "--new-key", "new-pass"],
    )
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_verify_cmd_valid_key(runner: CliRunner, setup_profile: Path) -> None:
    result = runner.invoke(
        rotate_group,
        ["verify", "myapp", "--key", "old-pass"],
    )
    assert result.exit_code == 0
    assert "valid" in result.output


def test_verify_cmd_invalid_key_exits_nonzero(runner: CliRunner, setup_profile: Path) -> None:
    result = runner.invoke(
        rotate_group,
        ["verify", "myapp", "--key", "bad-key"],
    )
    assert result.exit_code != 0
    assert "invalid" in result.output
