"""Tests for envault.import_env."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.import_env import ImportError, _parse_dotenv, _parse_json, import_env
from envault.vault import load_vault


# ---------------------------------------------------------------------------
# Unit tests for parsers
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic():
    text = "KEY=value\nFOO=bar\n"
    assert _parse_dotenv(text) == {"KEY": "value", "FOO": "bar"}


def test_parse_dotenv_strips_quotes():
    text = 'DB_URL="postgres://localhost/db"\nTOKEN=\'secret\'\n'
    result = _parse_dotenv(text)
    assert result["DB_URL"] == "postgres://localhost/db"
    assert result["TOKEN"] == "secret"


def test_parse_dotenv_ignores_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    assert _parse_dotenv(text) == {"KEY": "val"}


def test_parse_dotenv_skips_lines_without_equals():
    text = "NOEQUALS\nGOOD=yes\n"
    assert _parse_dotenv(text) == {"GOOD": "yes"}


def test_parse_json_basic():
    text = json.dumps({"A": "1", "B": "hello"})
    assert _parse_json(text) == {"A": "1", "B": "hello"}


def test_parse_json_coerces_values_to_str():
    text = json.dumps({"PORT": 8080, "DEBUG": True})
    result = _parse_json(text)
    assert result["PORT"] == "8080"
    assert result["DEBUG"] == "True"


def test_parse_json_invalid_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        _parse_json("not json")


def test_parse_json_non_object_raises():
    with pytest.raises(ImportError, match="object"):
        _parse_json(json.dumps(["a", "b"]))


# ---------------------------------------------------------------------------
# Integration tests for import_env
# ---------------------------------------------------------------------------

MASTER_KEY = "test-master-key-import"


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


def test_import_dotenv_creates_vault(tmp_path: Path, tmp_vault: Path):
    src = tmp_path / ".env"
    src.write_text("HELLO=world\nFOO=bar\n")
    result = import_env(src, tmp_vault, MASTER_KEY, fmt="dotenv")
    assert result == {"HELLO": "world", "FOO": "bar"}
    assert tmp_vault.exists()
    assert load_vault(tmp_vault, MASTER_KEY) == {"HELLO": "world", "FOO": "bar"}


def test_import_json_creates_vault(tmp_path: Path, tmp_vault: Path):
    src = tmp_path / "secrets.json"
    src.write_text(json.dumps({"API_KEY": "abc123", "TIMEOUT": "30"}))
    result = import_env(src, tmp_vault, MASTER_KEY, fmt="json")
    assert result["API_KEY"] == "abc123"
    assert load_vault(tmp_vault, MASTER_KEY)["TIMEOUT"] == "30"


def test_import_merge_preserves_existing_keys(tmp_path: Path, tmp_vault: Path):
    from envault.vault import save_vault
    save_vault(tmp_vault, {"EXISTING": "keep", "OVERRIDE": "old"}, MASTER_KEY)
    src = tmp_path / ".env"
    src.write_text("OVERRIDE=new\nNEW_KEY=added\n")
    result = import_env(src, tmp_vault, MASTER_KEY, fmt="dotenv", merge=True)
    assert result["EXISTING"] == "keep"
    assert result["OVERRIDE"] == "new"
    assert result["NEW_KEY"] == "added"


def test_import_missing_source_raises(tmp_path: Path, tmp_vault: Path):
    with pytest.raises(ImportError, match="Source file not found"):
        import_env(tmp_path / "ghost.env", tmp_vault, MASTER_KEY)


def test_import_unknown_format_raises(tmp_path: Path, tmp_vault: Path):
    src = tmp_path / "data.toml"
    src.write_text("key = 'value'\n")
    with pytest.raises(ImportError, match="Unknown format"):
        import_env(src, tmp_vault, MASTER_KEY, fmt="toml")
