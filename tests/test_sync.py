"""Tests for envault.sync — push/pull vault files to/from a shared directory."""

import json
import pytest
from pathlib import Path

from envault.sync import push, pull, list_remote, SYNC_MANIFEST


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "local" / "default.vault"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"ENCRYPTED_BLOB_CONTENT")
    return p


@pytest.fixture()
def sync_dir(tmp_path: Path) -> Path:
    return tmp_path / "shared"


def test_push_creates_vault_in_sync_dir(vault_file, sync_dir):
    dest = push("default", vault_file, sync_dir)
    assert dest.exists()
    assert dest.read_bytes() == b"ENCRYPTED_BLOB_CONTENT"


def test_push_creates_sync_dir_if_missing(vault_file, sync_dir):
    assert not sync_dir.exists()
    push("default", vault_file, sync_dir)
    assert sync_dir.exists()


def test_push_updates_manifest(vault_file, sync_dir):
    push("default", vault_file, sync_dir)
    manifest = json.loads((sync_dir / SYNC_MANIFEST).read_text())
    assert "default" in manifest
    assert "pushed_at" in manifest["default"]
    assert manifest["default"]["size"] > 0


def test_pull_restores_vault_locally(vault_file, sync_dir, tmp_path):
    push("default", vault_file, sync_dir)
    local_dest = tmp_path / "restored" / "default.vault"
    result = pull("default", sync_dir, local_dest)
    assert result == local_dest
    assert local_dest.read_bytes() == b"ENCRYPTED_BLOB_CONTENT"


def test_pull_creates_parent_dirs(vault_file, sync_dir, tmp_path):
    push("default", vault_file, sync_dir)
    deep_path = tmp_path / "a" / "b" / "c" / "default.vault"
    pull("default", sync_dir, deep_path)
    assert deep_path.exists()


def test_pull_missing_profile_raises(sync_dir, tmp_path):
    sync_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        pull("nonexistent", sync_dir, tmp_path / "out.vault")


def test_list_remote_returns_manifest(vault_file, sync_dir):
    push("default", vault_file, sync_dir)
    push("staging", vault_file, sync_dir)
    entries = list_remote(sync_dir)
    assert set(entries.keys()) == {"default", "staging"}


def test_list_remote_empty_when_no_manifest(sync_dir):
    sync_dir.mkdir()
    assert list_remote(sync_dir) == {}


def test_push_overwrites_previous(vault_file, sync_dir):
    push("default", vault_file, sync_dir)
    vault_file.write_bytes(b"NEW_CONTENT")
    push("default", vault_file, sync_dir)
    dest = sync_dir / "default.vault"
    assert dest.read_bytes() == b"NEW_CONTENT"
