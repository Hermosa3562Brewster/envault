"""Tests for envault.template — template rendering with vault secrets."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.template import TemplateError, render_file, render_string
from envault.vault import save_vault


SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "s3cr3t"}


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------

def test_render_string_substitutes_known_keys():
    result = render_string("host={{ DB_HOST }} port={{ DB_PORT }}", SECRETS)
    assert result == "host=localhost port=5432"


def test_render_string_handles_extra_whitespace_in_placeholder():
    result = render_string("key={{  API_KEY  }}", SECRETS)
    assert result == "key=s3cr3t"


def test_render_string_no_placeholders_returns_unchanged():
    text = "nothing to replace here"
    assert render_string(text, SECRETS) == text


def test_render_string_strict_raises_on_unknown_key():
    with pytest.raises(TemplateError, match="UNKNOWN"):
        render_string("value={{ UNKNOWN }}", SECRETS, strict=True)


def test_render_string_non_strict_leaves_unknown_placeholder():
    result = render_string("value={{ UNKNOWN }}", SECRETS, strict=False)
    assert result == "value={{ UNKNOWN }}"


def test_render_string_multiple_occurrences_of_same_key():
    result = render_string("{{ DB_HOST }}:{{ DB_HOST }}", SECRETS)
    assert result == "localhost:localhost"


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    save_vault(vf, SECRETS, "masterpass")
    return vf


def test_render_file_returns_rendered_content(tmp_path: Path, vault_file: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("DB={{ DB_HOST }}:{{ DB_PORT }}")
    result = render_file(tpl, vault_file, "masterpass")
    assert result == "DB=localhost:5432"


def test_render_file_writes_output_file(tmp_path: Path, vault_file: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("API={{ API_KEY }}")
    out = tmp_path / "config.rendered"
    render_file(tpl, vault_file, "masterpass", output_path=out)
    assert out.read_text() == "API=s3cr3t"


def test_render_file_missing_template_raises(tmp_path: Path, vault_file: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "ghost.tpl", vault_file, "masterpass")


def test_render_file_wrong_key_raises(tmp_path: Path, vault_file: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("DB={{ DB_HOST }}")
    with pytest.raises(ValueError):
        render_file(tpl, vault_file, "wrongpass")


def test_render_file_strict_unknown_placeholder(tmp_path: Path, vault_file: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("x={{ DOES_NOT_EXIST }}")
    with pytest.raises(TemplateError, match="DOES_NOT_EXIST"):
        render_file(tpl, vault_file, "masterpass", strict=True)
