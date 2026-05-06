"""Tests for envault.pin"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.pin import (
    PinError,
    _fingerprint,
    _pin_path,
    check_pin,
    get_pin,
    pin_key,
    remove_pin,
)


@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myprofile"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# _fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_is_16_hex_chars() -> None:
    fp = _fingerprint("supersecret")
    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)


def test_same_key_produces_same_fingerprint() -> None:
    assert _fingerprint("key") == _fingerprint("key")


def test_different_keys_produce_different_fingerprints() -> None:
    assert _fingerprint("key1") != _fingerprint("key2")


# ---------------------------------------------------------------------------
# pin_key / get_pin
# ---------------------------------------------------------------------------

def test_pin_key_creates_pin_file(profile_dir: Path) -> None:
    pin_key(profile_dir, "mykey")
    assert _pin_path(profile_dir).exists()


def test_pin_key_returns_fingerprint(profile_dir: Path) -> None:
    fp = pin_key(profile_dir, "mykey")
    assert fp == _fingerprint("mykey")


def test_get_pin_returns_none_when_missing(profile_dir: Path) -> None:
    assert get_pin(profile_dir) is None


def test_get_pin_returns_stored_fingerprint(profile_dir: Path) -> None:
    fp = pin_key(profile_dir, "mykey")
    assert get_pin(profile_dir) == fp


def test_get_pin_raises_on_corrupt_file(profile_dir: Path) -> None:
    _pin_path(profile_dir).write_text("not-json")
    with pytest.raises(PinError):
        get_pin(profile_dir)


# ---------------------------------------------------------------------------
# check_pin
# ---------------------------------------------------------------------------

def test_check_pin_returns_true_when_no_pin(profile_dir: Path) -> None:
    assert check_pin(profile_dir, "anykey") is True


def test_check_pin_returns_true_for_correct_key(profile_dir: Path) -> None:
    pin_key(profile_dir, "correctkey")
    assert check_pin(profile_dir, "correctkey") is True


def test_check_pin_returns_false_for_wrong_key(profile_dir: Path) -> None:
    pin_key(profile_dir, "correctkey")
    assert check_pin(profile_dir, "wrongkey") is False


# ---------------------------------------------------------------------------
# remove_pin
# ---------------------------------------------------------------------------

def test_remove_pin_deletes_file(profile_dir: Path) -> None:
    pin_key(profile_dir, "mykey")
    assert remove_pin(profile_dir) is True
    assert not _pin_path(profile_dir).exists()


def test_remove_pin_returns_false_when_not_pinned(profile_dir: Path) -> None:
    assert remove_pin(profile_dir) is False


def test_remove_then_get_returns_none(profile_dir: Path) -> None:
    pin_key(profile_dir, "mykey")
    remove_pin(profile_dir)
    assert get_pin(profile_dir) is None
