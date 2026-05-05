"""Tests for envault.lint."""
import pytest
from envault.lint import lint_env, LintIssue


def test_clean_env_produces_no_issues():
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"}
    result = lint_env(env)
    assert result.issues == []
    assert not result.has_errors


def test_blank_key_is_error():
    result = lint_env({"  ": "value"})
    errors = result.errors
    assert any("blank" in i.message.lower() for i in errors)


def test_key_with_spaces_is_error():
    result = lint_env({"MY KEY": "value"})
    assert result.has_errors
    assert any("spaces" in i.message.lower() for i in result.errors)


def test_lowercase_key_is_warning():
    result = lint_env({"my_key": "value"})
    warnings = result.warnings
    assert any("uppercase" in i.message.lower() for i in warnings)


def test_empty_value_is_warning():
    result = lint_env({"API_KEY": ""})
    warnings = result.warnings
    assert any("empty" in i.message.lower() for i in warnings)


def test_short_secret_is_warning():
    result = lint_env({"API_SECRET": "abc"})
    warnings = result.warnings
    assert any("short" in i.message.lower() for i in warnings)


def test_long_secret_no_warning():
    result = lint_env({"API_SECRET": "averylongsecretvalue123"})
    assert not any("short" in i.message.lower() for i in result.warnings)


def test_literal_backslash_n_is_info():
    result = lint_env({"CERT": "line1\\nline2"})
    infos = [i for i in result.issues if i.severity == "info"]
    assert any("newline" in i.message.lower() for i in infos)


def test_summary_counts_correctly():
    env = {
        "MY KEY": "x",       # error: spaces in key
        "lowercase": "val",  # warning: not uppercase
        "EMPTY": "",         # warning: empty value
    }
    result = lint_env(env)
    assert result.has_errors
    assert len(result.errors) == 1
    assert len(result.warnings) >= 2
    summary = result.summary()
    assert "1 error" in summary


def test_multiple_issues_on_same_key():
    # lowercase key AND empty value → two issues for same key
    result = lint_env({"my_secret": ""})
    keys_reported = [i.key for i in result.issues]
    assert keys_reported.count("my_secret") >= 2
