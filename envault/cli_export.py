"""CLI commands for exporting decrypted vault contents."""

from __future__ import annotations

import sys

import click

from .export import SUPPORTED_FORMATS, ExportError, export_env
from .profiles import get_profile
from .vault import load_vault


@click.group(name="export")
def export_group() -> None:
    """Export decrypted secrets in various formats."""


@export_group.command(name="env")
@click.argument("profile")
@click.option(
    "--key",
    envvar="ENVAULT_MASTER_KEY",
    required=True,
    help="Master key (or set ENVAULT_MASTER_KEY).",
)
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    default="-",
    help="File path to write output (default: stdout).",
    type=click.Path(dir_okay=False, writable=True),
)
def export_cmd(profile: str, key: str, fmt: str, output: str) -> None:
    """Decrypt PROFILE vault and emit secrets in the chosen FORMAT."""
    info = get_profile(profile)
    if info is None:
        click.echo(f"Profile '{profile}' not found.", err=True)
        sys.exit(1)

    vault_path = info["vault_path"]

    try:
        env = load_vault(vault_path, key)
    except (ValueError, FileNotFoundError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    try:
        text = export_env(env, fmt.lower())
    except ExportError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output == "-":
        click.echo(text, nl=False)
    else:
        with open(output, "w") as fh:
            fh.write(text)
        click.echo(f"Exported {len(env)} variable(s) to {output}")
