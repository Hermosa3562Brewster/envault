"""CLI commands for key rotation."""

from __future__ import annotations

from pathlib import Path

import click

from .profiles import load_index
from .rotate import RotationError, rotate_vault


@click.group("rotate")
def rotate_group() -> None:
    """Rotate the master key for a vault."""


@rotate_group.command("key")
@click.argument("profile")
@click.option(
    "--old-key",
    prompt=True,
    hide_input=True,
    help="Current master key.",
)
@click.option(
    "--new-key",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New master key.",
)
def rotate_key_cmd(profile: str, old_key: str, new_key: str) -> None:
    """Re-encrypt PROFILE's vault under a new master key."""
    index = load_index()
    if profile not in index:
        raise click.ClickException(f"Unknown profile '{profile}'. Run 'envault profiles list'.")

    vault_path = Path(index[profile]["vault_path"])
    try:
        rotate_vault(vault_path, old_key, new_key, profile=profile)
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"✓ Key rotated successfully for profile '{profile}'.", fg="green")


@rotate_group.command("verify")
@click.argument("profile")
@click.option(
    "--key",
    prompt=True,
    hide_input=True,
    help="Master key to verify.",
)
def verify_cmd(profile: str, key: str) -> None:
    """Check whether KEY can decrypt PROFILE's vault."""
    index = load_index()
    if profile not in index:
        raise click.ClickException(f"Unknown profile '{profile}'.")

    from .rotate import verify_key

    vault_path = Path(index[profile]["vault_path"])
    if verify_key(vault_path, key):
        click.secho("✓ Key is valid.", fg="green")
    else:
        click.secho("✗ Key is invalid or vault is missing.", fg="red")
        raise SystemExit(1)
