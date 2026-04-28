"""Export decrypted .env contents to various formats (shell, JSON, dotenv)."""

from __future__ import annotations

import json
import shlex
from typing import Dict

SUPPORTED_FORMATS = ("dotenv", "shell", "json")


class ExportError(ValueError):
    """Raised when an unsupported export format is requested."""


def export_dotenv(env: Dict[str, str]) -> str:
    """Return standard KEY=VALUE lines, values quoted if necessary."""
    lines = []
    for key, value in sorted(env.items()):
        # Quote the value if it contains spaces or special characters
        if any(c in value for c in (" ", "\t", "\n", "'", '"', "$", "`", "\\")):
            quoted = shlex.quote(value)
        else:
            quoted = value
        lines.append(f"{key}={quoted}")
    return "\n".join(lines) + ("\n" if lines else "")


def export_shell(env: Dict[str, str]) -> str:
    """Return 'export KEY=VALUE' lines suitable for sourcing in a shell."""
    lines = []
    for key, value in sorted(env.items()):
        quoted = shlex.quote(value)
        lines.append(f"export {key}={quoted}")
    return "\n".join(lines) + ("\n" if lines else "")


def export_json(env: Dict[str, str]) -> str:
    """Return a pretty-printed JSON object of the environment."""
    return json.dumps(env, indent=2, sort_keys=True) + "\n"


def export_env(env: Dict[str, str], fmt: str) -> str:
    """Dispatch to the correct exporter based on *fmt*.

    Parameters
    ----------
    env:
        Mapping of environment variable names to values.
    fmt:
        One of ``'dotenv'``, ``'shell'``, or ``'json'``.

    Returns
    -------
    str
        The formatted output ready to write to stdout or a file.

    Raises
    ------
    ExportError
        If *fmt* is not a recognised format.
    """
    if fmt == "dotenv":
        return export_dotenv(env)
    if fmt == "shell":
        return export_shell(env)
    if fmt == "json":
        return export_json(env)
    raise ExportError(
        f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
