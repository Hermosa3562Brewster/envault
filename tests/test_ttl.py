"""Tests for envault.ttl — TTL / expiry support."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.ttl import (
    TTLError,
    TTLRecord,
    check_ttl,
    clear_ttl,
    get_ttl,
    set_ttl,
)


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myprofile"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# TTLRecord unit tests
# ---------------------------------------------------------------------------

def test_ttl_record_expired_when_past_expiry():
    record = TTLRecord(expires_at=time.time() - 10)
    assert record.is_expired()


def test_ttl_record_not_expired_when_future():
    record = TTLRecord(expires_at=time.time() + 3600)
    assert not record.is_expired()


def test_ttl_record_seconds_remaining_positive():
    future = time.time() + 100
    record = TTLRecord(expires_at=future)
    remaining = record.seconds_remaining()
    assert 0 < remaining <= 100


def test_ttl_record_seconds_remaining_zero_when_expired():
    record = TTLRecord(expires_at=time.time() - 50)
    assert record.seconds_remaining() == 0.0


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------

def test_set_ttl_creates_file(profile_dir: Path):
    expiry = time.time() + 3600
    set_ttl(profile_dir, expires_at=expiry, note="rotate soon")
    assert (profile_dir / ".ttl.json").exists()


def test_get_ttl_returns_none_when_no_file(profile_dir: Path):
    assert get_ttl(profile_dir) is None


def test_set_and_get_ttl_round_trip(profile_dir: Path):
    expiry = time.time() + 7200
    set_ttl(profile_dir, expires_at=expiry, note="my note")
    record = get_ttl(profile_dir)
    assert record is not None
    assert abs(record.expires_at - expiry) < 0.001
    assert record.note == "my note"


def test_clear_ttl_removes_file(profile_dir: Path):
    set_ttl(profile_dir, expires_at=time.time() + 60)
    result = clear_ttl(profile_dir)
    assert result is True
    assert not (profile_dir / ".ttl.json").exists()


def test_clear_ttl_returns_false_when_no_file(profile_dir: Path):
    assert clear_ttl(profile_dir) is False


def test_set_ttl_raises_for_missing_directory(tmp_path: Path):
    with pytest.raises(TTLError):
        set_ttl(tmp_path / "nonexistent", expires_at=time.time() + 60)


# ---------------------------------------------------------------------------
# check_ttl tests
# ---------------------------------------------------------------------------

def test_check_ttl_returns_none_when_no_record(profile_dir: Path):
    assert check_ttl(profile_dir) is None


def test_check_ttl_returns_none_when_not_yet_expired(profile_dir: Path):
    set_ttl(profile_dir, expires_at=time.time() + 3600)
    assert check_ttl(profile_dir) is None


def test_check_ttl_returns_record_when_expired(profile_dir: Path):
    past = time.time() - 1
    set_ttl(profile_dir, expires_at=past, note="stale")
    result = check_ttl(profile_dir)
    assert result is not None
    assert result.note == "stale"
    assert result.is_expired()
