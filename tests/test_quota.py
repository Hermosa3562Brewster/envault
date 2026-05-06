"""Tests for envault.quota."""
import pytest
from pathlib import Path

from envault.quota import (
    QuotaError,
    QuotaRecord,
    DEFAULT_QUOTA,
    load_quota,
    save_quota,
    set_limit,
    remove_override,
    check_quota,
    effective_limit,
)


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myprofile"
    d.mkdir()
    return d


def test_load_quota_missing_file_returns_defaults(profile_dir):
    record = load_quota(profile_dir)
    assert record.limit == DEFAULT_QUOTA
    assert record.overrides == {}


def test_save_and_load_round_trip(profile_dir):
    record = QuotaRecord(limit=50, overrides={"SECRET_KEY": 1})
    save_quota(profile_dir, record)
    loaded = load_quota(profile_dir)
    assert loaded.limit == 50
    assert loaded.overrides == {"SECRET_KEY": 1}


def test_set_limit_global(profile_dir):
    set_limit(profile_dir, 25)
    assert load_quota(profile_dir).limit == 25


def test_set_limit_per_key(profile_dir):
    set_limit(profile_dir, 3, key="DB_PASSWORD")
    record = load_quota(profile_dir)
    assert record.overrides["DB_PASSWORD"] == 3
    assert record.limit == DEFAULT_QUOTA


def test_set_limit_zero_raises(profile_dir):
    with pytest.raises(QuotaError, match="at least 1"):
        set_limit(profile_dir, 0)


def test_remove_override_deletes_key(profile_dir):
    set_limit(profile_dir, 5, key="API_KEY")
    remove_override(profile_dir, "API_KEY")
    record = load_quota(profile_dir)
    assert "API_KEY" not in record.overrides


def test_remove_override_missing_key_raises(profile_dir):
    with pytest.raises(QuotaError, match="No override found"):
        remove_override(profile_dir, "NONEXISTENT")


def test_check_quota_below_limit(profile_dir):
    set_limit(profile_dir, 5)
    env = {f"K{i}": str(i) for i in range(4)}
    assert check_quota(profile_dir, env) is False


def test_check_quota_at_limit(profile_dir):
    set_limit(profile_dir, 5)
    env = {f"K{i}": str(i) for i in range(5)}
    assert check_quota(profile_dir, env) is True


def test_check_quota_uses_key_override(profile_dir):
    set_limit(profile_dir, 100)
    set_limit(profile_dir, 2, key="SPECIAL")
    env = {"A": "1", "B": "2"}
    assert check_quota(profile_dir, env, key="SPECIAL") is True
    assert check_quota(profile_dir, env, key="OTHER") is False


def test_effective_limit_global(profile_dir):
    set_limit(profile_dir, 42)
    assert effective_limit(profile_dir) == 42


def test_effective_limit_key_override(profile_dir):
    set_limit(profile_dir, 42)
    set_limit(profile_dir, 7, key="TOKEN")
    assert effective_limit(profile_dir, key="TOKEN") == 7
    assert effective_limit(profile_dir, key="OTHER") == 42


def test_load_corrupt_json_raises(profile_dir):
    (profile_dir / ".quota.json").write_text("{not valid json")
    with pytest.raises(QuotaError, match="Corrupt quota file"):
        load_quota(profile_dir)
