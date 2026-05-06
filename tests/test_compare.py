"""Tests for envault.compare module."""
import json
from pathlib import Path

import pytest

from envault.vault import save_vault
from envault.compare import (
    compare_vaults,
    compare_profiles,
    CompareError,
    CompareResult,
    summary_lines,
    _compare_dicts,
)

MASTER_KEY = "test-master-key-compare"


@pytest.fixture()
def vault_pair(tmp_path):
    left = tmp_path / "left.vault"
    right = tmp_path / "right.vault"
    return left, right


def _make_vault(path: Path, env: dict, key: str = MASTER_KEY):
    save_vault(path, env, key)


# --- _compare_dicts unit tests ---

def test_identical_dicts_produce_no_differences():
    result = _compare_dicts({"A": "1", "B": "2"}, {"A": "1", "B": "2"})
    assert not result.has_differences
    assert result.identical == {"A": "1", "B": "2"}


def test_only_in_left_detected():
    result = _compare_dicts({"A": "1", "X": "old"}, {"A": "1"})
    assert "X" in result.only_in_left
    assert result.only_in_right == {}


def test_only_in_right_detected():
    result = _compare_dicts({"A": "1"}, {"A": "1", "NEW": "val"})
    assert "NEW" in result.only_in_right


def test_changed_values_detected():
    result = _compare_dicts({"A": "old"}, {"A": "new"})
    assert "A" in result.changed
    assert result.changed["A"] == ("old", "new")


def test_has_differences_false_when_identical():
    result = CompareResult(identical={"K": "v"})
    assert not result.has_differences


def test_has_differences_true_when_changed():
    result = CompareResult(changed={"K": ("a", "b")})
    assert result.has_differences


# --- compare_vaults integration tests ---

def test_compare_vaults_identical(vault_pair):
    left, right = vault_pair
    env = {"DB_HOST": "localhost", "PORT": "5432"}
    _make_vault(left, env)
    _make_vault(right, env)
    result = compare_vaults(left, right, MASTER_KEY)
    assert not result.has_differences


def test_compare_vaults_detects_changes(vault_pair):
    left, right = vault_pair
    _make_vault(left, {"A": "1", "B": "old"})
    _make_vault(right, {"A": "1", "B": "new", "C": "extra"})
    result = compare_vaults(left, right, MASTER_KEY)
    assert "B" in result.changed
    assert "C" in result.only_in_right


def test_compare_vaults_missing_left_raises(tmp_path):
    right = tmp_path / "right.vault"
    _make_vault(right, {"A": "1"})
    with pytest.raises(CompareError, match="Left vault not found"):
        compare_vaults(tmp_path / "ghost.vault", right, MASTER_KEY)


def test_compare_vaults_missing_right_raises(tmp_path):
    left = tmp_path / "left.vault"
    _make_vault(left, {"A": "1"})
    with pytest.raises(CompareError, match="Right vault not found"):
        compare_vaults(left, tmp_path / "ghost.vault", MASTER_KEY)


# --- summary_lines tests ---

def test_summary_lines_no_diff():
    result = CompareResult(identical={"A": "1"})
    lines = summary_lines(result)
    assert any("no differences" in l for l in lines)


def test_summary_lines_shows_labels():
    result = CompareResult(only_in_left={"X": "v"})
    lines = summary_lines(result, left_label="staging", right_label="prod")
    assert any("staging" in l for l in lines)
