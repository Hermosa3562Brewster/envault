"""Import secrets into a vault from various external formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from envault.vault import save_vault


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-style file into a key/value dict."""
    result: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes (single or double)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into a key/value dict (values coerced to str)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    return {str(k): str(v) for k, v in data.items()}


def import_env(
    source: Path,
    vault_path: Path,
    master_key: str,
    fmt: str = "dotenv",
    merge: bool = False,
) -> Dict[str, str]:
    """Import a source file into a vault.

    Args:
        source:     Path to the source secrets file.
        vault_path: Destination vault file.
        master_key: Encryption key.
        fmt:        Source format — ``'dotenv'`` or ``'json'``.
        merge:      If *True* and the vault already exists, merge rather than
                    overwrite existing keys.

    Returns:
        The final dict of key/value pairs written to the vault.
    """
    if not source.exists():
        raise ImportError(f"Source file not found: {source}")

    text = source.read_text(encoding="utf-8")

    parsers = {"dotenv": _parse_dotenv, "json": _parse_json}
    if fmt not in parsers:
        raise ImportError(f"Unknown format '{fmt}'. Choose from: {list(parsers)}.")

    incoming = parsers[fmt](text)

    if merge and vault_path.exists():
        from envault.vault import load_vault  # avoid circular at module level
        existing = load_vault(vault_path, master_key)
        existing.update(incoming)
        final = existing
    else:
        final = incoming

    save_vault(vault_path, final, master_key)
    return final
