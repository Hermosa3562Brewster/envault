"""CLI entry-point for envault, with multi-profile support."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault import vault, profiles as prof


@click.group()
def cli() -> None:
    """envault — local secrets manager."""


# ---------------------------------------------------------------------------
# lock
# ---------------------------------------------------------------------------

@cli.command("lock")
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.option("--password", "-p", prompt=True, hide_input=True, help="Master password")
@click.option("--profile", default=prof.DEFAULT_PROFILE, show_default=True, help="Named profile")
def lock_cmd(env_file: str, password: str, profile: str) -> None:
    """Encrypt ENV_FILE into a vault."""
    env_path = Path(env_file)
    vault_path = vault.lock(env_path, password, profile=profile)
    click.echo(f"Locked → {vault_path}  (profile: {profile})")


# ---------------------------------------------------------------------------
# unlock
# ---------------------------------------------------------------------------

@cli.command("unlock")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Master password")
@click.option("--profile", default=prof.DEFAULT_PROFILE, show_default=True, help="Named profile")
@click.option("--out", "env_out", default=None, help="Output .env path")
def unlock_cmd(password: str, profile: str, env_out: str | None) -> None:
    """Decrypt a vault back to a .env file."""
    base_dir = Path(".")
    vault_path = prof.resolve_vault_path(base_dir, profile)
    if vault_path is None:
        click.echo(f"No vault registered for profile '{profile}'.", err=True)
        sys.exit(1)

    env_path = Path(env_out) if env_out else None
    try:
        out = vault.unlock(vault_path, password, env_path=env_path, profile=profile)
    except ValueError:
        click.echo("Error: wrong password or corrupted vault.", err=True)
        sys.exit(1)

    click.echo(f"Unlocked → {out}  (profile: {profile})")


# ---------------------------------------------------------------------------
# view
# ---------------------------------------------------------------------------

@cli.command("view")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Master password")
@click.option("--profile", default=prof.DEFAULT_PROFILE, show_default=True, help="Named profile")
def view_cmd(password: str, profile: str) -> None:
    """Print decrypted secrets without writing to disk."""
    base_dir = Path(".")
    vault_path = prof.resolve_vault_path(base_dir, profile)
    if vault_path is None:
        click.echo(f"No vault registered for profile '{profile}'.", err=True)
        sys.exit(1)

    try:
        env_vars = vault.view(vault_path, password)
    except ValueError:
        click.echo("Error: wrong password or corrupted vault.", err=True)
        sys.exit(1)

    for key, value in env_vars.items():
        click.echo(f"{key}={value}")


# ---------------------------------------------------------------------------
# list-profiles
# ---------------------------------------------------------------------------

@cli.command("list-profiles")
def list_profiles_cmd() -> None:
    """List all profiles registered in the current directory."""
    base_dir = Path(".")
    registered = prof.list_profiles(base_dir)
    if not registered:
        click.echo("No profiles registered.")
        return
    for name in registered:
        marker = " (default)" if name == prof.DEFAULT_PROFILE else ""
        click.echo(f"  {name}{marker}")
