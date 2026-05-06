"""Tests for envault.alias."""
import pytest
from pathlib import Path
from envault.alias import (
    AliasError,
    load_aliases,
    save_aliases,
    set_alias,
    remove_alias,
    resolve,
    list_aliases,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_aliases_missing_file_returns_empty(base_dir):
    assert load_aliases(base_dir) == {}


def test_save_and_load_round_trip(base_dir):
    aliases = {"prod": "production", "dev": "development"}
    save_aliases(base_dir, aliases)
    assert load_aliases(base_dir) == aliases


def test_set_alias_creates_entry(base_dir):
    set_alias(base_dir, "p", "production")
    assert load_aliases(base_dir)["p"] == "production"


def test_set_alias_overwrites_existing(base_dir):
    set_alias(base_dir, "p", "production")
    set_alias(base_dir, "p", "staging")
    assert load_aliases(base_dir)["p"] == "staging"


def test_set_alias_blank_name_raises(base_dir):
    with pytest.raises(AliasError, match="blank"):
        set_alias(base_dir, "  ", "production")


def test_set_alias_same_as_profile_raises(base_dir):
    with pytest.raises(AliasError, match="differ"):
        set_alias(base_dir, "production", "production")


def test_remove_alias_deletes_entry(base_dir):
    set_alias(base_dir, "p", "production")
    remove_alias(base_dir, "p")
    assert "p" not in load_aliases(base_dir)


def test_remove_alias_missing_raises(base_dir):
    with pytest.raises(AliasError, match="not found"):
        remove_alias(base_dir, "ghost")


def test_resolve_returns_alias_target(base_dir):
    set_alias(base_dir, "p", "production")
    assert resolve(base_dir, "p") == "production"


def test_resolve_returns_name_when_no_alias(base_dir):
    assert resolve(base_dir, "production") == "production"


def test_list_aliases_returns_all(base_dir):
    set_alias(base_dir, "p", "production")
    set_alias(base_dir, "s", "staging")
    result = list_aliases(base_dir)
    assert result == {"p": "production", "s": "staging"}


def test_load_corrupt_json_raises_alias_error(base_dir):
    path = base_dir / ".envault" / "aliases.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(AliasError, match="Corrupt"):
        load_aliases(base_dir)


def test_load_non_object_json_raises_alias_error(base_dir):
    path = base_dir / ".envault" / "aliases.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[1, 2, 3]")
    with pytest.raises(AliasError, match="JSON object"):
        load_aliases(base_dir)
