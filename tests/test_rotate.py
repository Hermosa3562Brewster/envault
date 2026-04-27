"""Tests for envault.rotate."""

from pathlib import Path

import pytest

from envault.rotate import RotationError, rotate_vault, verify_key
from envault.vault import load_vault, save_vault


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env_vars = {"APP_ENV": "production", "SECRET": "s3cr3t"}
    path = tmp_path / "test.vault"
    save_vault(env_vars, path, "old-master-key")
    return path


def test_rotate_vault_re_encrypts_with_new_key(vault_file: Path) -> None:
    rotate_vault(vault_file, "old-master-key", "new-master-key")
    env_vars = load_vault(vault_file, "new-master-key")
    assert env_vars["APP_ENV"] == "production"
    assert env_vars["SECRET"] == "s3cr3t"


def test_rotate_vault_old_key_no_longer_works(vault_file: Path) -> None:
    rotate_vault(vault_file, "old-master-key", "new-master-key")
    with pytest.raises(ValueError):
        load_vault(vault_file, "old-master-key")


def test_rotate_vault_wrong_old_key_raises_rotation_error(vault_file: Path) -> None:
    with pytest.raises(RotationError, match="Old key is incorrect"):
        rotate_vault(vault_file, "wrong-key", "new-master-key")


def test_rotate_vault_missing_file_raises_rotation_error(tmp_path: Path) -> None:
    missing = tmp_path / "ghost.vault"
    with pytest.raises(RotationError, match="Vault file not found"):
        rotate_vault(missing, "old", "new")


def test_rotate_vault_writes_audit_entry(vault_file: Path) -> None:
    from envault.audit import read_log

    rotate_vault(vault_file, "old-master-key", "new-master-key", profile="prod")
    entries = read_log(vault_file.parent)
    assert len(entries) == 1
    assert entries[0]["action"] == "rotate"
    assert entries[0]["profile"] == "prod"


def test_verify_key_returns_true_for_correct_key(vault_file: Path) -> None:
    assert verify_key(vault_file, "old-master-key") is True


def test_verify_key_returns_false_for_wrong_key(vault_file: Path) -> None:
    assert verify_key(vault_file, "bad-key") is False


def test_verify_key_returns_false_for_missing_file(tmp_path: Path) -> None:
    assert verify_key(tmp_path / "no.vault", "any-key") is False
