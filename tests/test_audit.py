"""Tests for envault.audit."""

import pytest
from pathlib import Path
from envault.audit import record, read_log, clear_log, ACTIONS


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def test_record_creates_log_file(audit_dir):
    record("dev", "lock", audit_dir=audit_dir)
    assert (audit_dir / "dev.log").exists()


def test_read_log_empty_when_no_file(audit_dir):
    assert read_log("dev", audit_dir=audit_dir) == []


def test_record_and_read_single_entry(audit_dir):
    record("dev", "unlock", audit_dir=audit_dir)
    entries = read_log("dev", audit_dir=audit_dir)
    assert len(entries) == 1
    assert entries[0]["action"] == "unlock"
    assert entries[0]["profile"] == "dev"
    assert "ts" in entries[0]
    assert "user" in entries[0]


def test_record_multiple_entries_ordered(audit_dir):
    for action in ("lock", "unlock", "view"):
        record("staging", action, audit_dir=audit_dir)
    entries = read_log("staging", audit_dir=audit_dir)
    assert len(entries) == 3
    assert [e["action"] for e in entries] == ["lock", "unlock", "view"]


def test_record_with_details(audit_dir):
    record("prod", "rotate", details={"keys_changed": 3}, audit_dir=audit_dir)
    entries = read_log("prod", audit_dir=audit_dir)
    assert entries[0]["details"] == {"keys_changed": 3}


def test_read_log_limit(audit_dir):
    for _ in range(10):
        record("dev", "view", audit_dir=audit_dir)
    entries = read_log("dev", audit_dir=audit_dir, limit=3)
    assert len(entries) == 3


def test_unknown_action_raises(audit_dir):
    with pytest.raises(ValueError, match="Unknown audit action"):
        record("dev", "explode", audit_dir=audit_dir)


def test_clear_log_removes_file(audit_dir):
    record("dev", "lock", audit_dir=audit_dir)
    clear_log("dev", audit_dir=audit_dir)
    assert not (audit_dir / "dev.log").exists()


def test_clear_log_noop_when_missing(audit_dir):
    # Should not raise even if log does not exist
    clear_log("nonexistent", audit_dir=audit_dir)


def test_profiles_are_isolated(audit_dir):
    record("dev", "lock", audit_dir=audit_dir)
    record("prod", "unlock", audit_dir=audit_dir)
    assert len(read_log("dev", audit_dir=audit_dir)) == 1
    assert len(read_log("prod", audit_dir=audit_dir)) == 1
    assert read_log("dev", audit_dir=audit_dir)[0]["action"] == "lock"
    assert read_log("prod", audit_dir=audit_dir)[0]["action"] == "unlock"
