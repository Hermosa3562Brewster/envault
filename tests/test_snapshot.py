"""Tests for envault.snapshot and envault.cli_snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.snapshot import (
    SnapshotError,
    _snapshots_dir,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)
from envault.cli_snapshot import snapshot_group


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"fake-encrypted-data-v1")
    return vf


# ---------------------------------------------------------------------------
# Unit tests for snapshot module
# ---------------------------------------------------------------------------

def test_create_snapshot_copies_vault(vault_file):
    snap = create_snapshot(vault_file, "before-deploy")
    assert snap.exists()
    assert snap.read_bytes() == vault_file.read_bytes()


def test_create_snapshot_records_in_index(vault_file):
    create_snapshot(vault_file, "snap1")
    snaps = list_snapshots(vault_file)
    names = [s["name"] for s in snaps]
    assert "snap1" in names


def test_list_snapshots_sorted_by_time(vault_file):
    create_snapshot(vault_file, "alpha")
    create_snapshot(vault_file, "beta")
    snaps = list_snapshots(vault_file)
    assert [s["name"] for s in snaps] == ["alpha", "beta"]


def test_restore_snapshot_overwrites_vault(vault_file):
    create_snapshot(vault_file, "v1")
    vault_file.write_bytes(b"modified-data")
    restore_snapshot(vault_file, "v1")
    assert vault_file.read_bytes() == b"fake-encrypted-data-v1"


def test_restore_missing_snapshot_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault_file, "ghost")


def test_delete_snapshot_removes_file_and_index(vault_file):
    create_snapshot(vault_file, "to-delete")
    delete_snapshot(vault_file, "to-delete")
    snaps = list_snapshots(vault_file)
    assert all(s["name"] != "to-delete" for s in snaps)
    snap_file = _snapshots_dir(vault_file) / "to-delete.vault"
    assert not snap_file.exists()


def test_delete_nonexistent_snapshot_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(vault_file, "nope")


def test_create_snapshot_missing_vault_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        create_snapshot(tmp_path / "missing.vault", "s1")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def setup_profile(tmp_path, monkeypatch):
    vault_path = tmp_path / "myapp.vault"
    vault_path.write_bytes(b"encrypted-blob")
    index = {"myapp": {"vault_path": str(vault_path)}}
    index_file = tmp_path / "index.json"
    index_file.write_text(json.dumps(index))
    monkeypatch.setattr("envault.profiles._index_path", lambda: index_file)
    monkeypatch.setattr("envault.cli_snapshot.load_index", lambda: index)
    return vault_path


def test_create_cmd_succeeds(runner, setup_profile):
    result = runner.invoke(snapshot_group, ["create", "myapp", "release-1"])
    assert result.exit_code == 0
    assert "release-1" in result.output


def test_list_cmd_shows_snapshot(runner, setup_profile):
    create_snapshot(setup_profile, "listed-snap")
    result = runner.invoke(snapshot_group, ["list", "myapp"])
    assert result.exit_code == 0
    assert "listed-snap" in result.output


def test_delete_cmd_succeeds(runner, setup_profile):
    create_snapshot(setup_profile, "temp")
    result = runner.invoke(snapshot_group, ["delete", "myapp", "temp"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_unknown_profile_exits_nonzero(runner, setup_profile):
    result = runner.invoke(snapshot_group, ["create", "unknown", "s1"])
    assert result.exit_code != 0
