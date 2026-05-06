"""Tests for envault.tag module."""
from __future__ import annotations

import json

import pytest

from envault.tag import (
    TagError,
    add_tag,
    all_tags,
    load_tags,
    profiles_by_tag,
    remove_tag,
    save_tags,
)


@pytest.fixture()
def profile_dir(tmp_path):
    d = tmp_path / "my_profile"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_tags_missing_file_returns_empty(profile_dir):
    assert load_tags(profile_dir) == []


def test_save_and_load_round_trip(profile_dir):
    save_tags(profile_dir, ["staging", "backend"])
    assert load_tags(profile_dir) == ["backend", "staging"]  # sorted


def test_save_deduplicates_tags(profile_dir):
    save_tags(profile_dir, ["prod", "prod", "staging"])
    assert load_tags(profile_dir) == ["prod", "staging"]


def test_load_corrupt_json_raises_tag_error(profile_dir):
    tags_path = profile_dir / ".envault" / "tags.json"
    tags_path.parent.mkdir(parents=True)
    tags_path.write_text("{not valid json")
    with pytest.raises(TagError, match="Invalid JSON"):
        load_tags(profile_dir)


def test_load_non_list_json_raises_tag_error(profile_dir):
    tags_path = profile_dir / ".envault" / "tags.json"
    tags_path.parent.mkdir(parents=True)
    tags_path.write_text(json.dumps({"tag": "oops"}))
    with pytest.raises(TagError, match="Corrupt"):
        load_tags(profile_dir)


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

def test_add_tag_creates_file(profile_dir):
    result = add_tag(profile_dir, "production")
    assert "production" in result
    assert load_tags(profile_dir) == ["production"]


def test_add_tag_is_idempotent(profile_dir):
    add_tag(profile_dir, "production")
    result = add_tag(profile_dir, "production")
    assert result.count("production") == 1


def test_add_empty_tag_raises_tag_error(profile_dir):
    with pytest.raises(TagError, match="not be empty"):
        add_tag(profile_dir, "   ")


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

def test_remove_tag_removes_it(profile_dir):
    save_tags(profile_dir, ["a", "b", "c"])
    result = remove_tag(profile_dir, "b")
    assert "b" not in result
    assert "a" in result and "c" in result


def test_remove_nonexistent_tag_raises_tag_error(profile_dir):
    save_tags(profile_dir, ["a"])
    with pytest.raises(TagError, match="not found"):
        remove_tag(profile_dir, "missing")


# ---------------------------------------------------------------------------
# profiles_by_tag / all_tags
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_dir(tmp_path):
    for name, tags in [
        ("alpha", ["production", "backend"]),
        ("beta", ["staging", "backend"]),
        ("gamma", ["production"]),
    ]:
        d = tmp_path / name
        d.mkdir()
        save_tags(d, tags)
    return tmp_path


def test_profiles_by_tag_returns_matching(base_dir):
    result = profiles_by_tag(base_dir, "production")
    assert result == ["alpha", "gamma"]


def test_profiles_by_tag_no_match_returns_empty(base_dir):
    assert profiles_by_tag(base_dir, "nonexistent") == []


def test_profiles_by_tag_missing_base_dir(tmp_path):
    assert profiles_by_tag(tmp_path / "nope", "x") == []


def test_all_tags_returns_mapping(base_dir):
    mapping = all_tags(base_dir)
    assert mapping["alpha"] == ["backend", "production"]
    assert mapping["beta"] == ["backend", "staging"]
    assert mapping["gamma"] == ["production"]


def test_all_tags_empty_base_dir(tmp_path):
    assert all_tags(tmp_path / "missing") == {}
