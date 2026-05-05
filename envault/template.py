"""Template rendering: substitute vault secrets into config file templates."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

from envault.vault import load_vault


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_string(template: str, secrets: Dict[str, str], strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *secrets*.

    Parameters
    ----------
    template:
        Raw template text containing ``{{ KEY }}`` placeholders.
    secrets:
        Mapping of variable names to their plaintext values.
    strict:
        When *True* (default) an unknown placeholder raises :class:`TemplateError`.
        When *False* unknown placeholders are left unchanged.
    """
    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in secrets:
            return secrets[key]
        if strict:
            raise TemplateError(f"Unknown placeholder: '{{{{{key}}}}}'")
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_replace, template)


def render_file(
    template_path: Path | str,
    vault_path: Path | str,
    master_key: str,
    output_path: Optional[Path | str] = None,
    strict: bool = True,
) -> str:
    """Render a template file by substituting secrets from a vault.

    Parameters
    ----------
    template_path:
        Path to the template file.
    vault_path:
        Path to the encrypted ``.vault`` file.
    master_key:
        Passphrase used to decrypt the vault.
    output_path:
        If provided the rendered content is written to this path.
    strict:
        Forwarded to :func:`render_string`.

    Returns
    -------
    str
        The fully rendered content.
    """
    template_path = Path(template_path)
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")

    secrets = load_vault(Path(vault_path), master_key)
    content = template_path.read_text(encoding="utf-8")
    rendered = render_string(content, secrets, strict=strict)

    if output_path is not None:
        Path(output_path).write_text(rendered, encoding="utf-8")

    return rendered
