"""CLI commands for syncing vaults to/from a shared directory."""

from __future__ import annotations

from pathlib import Path

import click

from envault.profiles import load_index
from envault.sync import push, pull, list_remote


@click.group("sync")
def sync_group():
    """Push and pull vault files to/from a shared sync directory."""


@sync_group.command("push")
@click.argument("profile")
@click.option(
    "--sync-dir",
    required=True,
    type=click.Path(file_okay=False, writable=True),
    help="Shared directory to push the vault into.",
)
def push_cmd(profile: str, sync_dir: str):
    """Push a locked vault to the shared sync directory."""
    index = load_index()
    if profile not in index:
        raise click.ClickException(f"Profile '{profile}' not found. Run 'envault lock' first.")

    vault_path = Path(index[profile]["vault_path"])
    if not vault_path.exists():
        raise click.ClickException(f"Vault file not found: {vault_path}")

    dest = push(profile, vault_path, Path(sync_dir))
    click.echo(f"Pushed '{profile}' vault to {dest}")


@sync_group.command("pull")
@click.argument("profile")
@click.option(
    "--sync-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Shared directory to pull the vault from.",
)
@click.option(
    "--vault-path",
    default=None,
    type=click.Path(dir_okay=False),
    help="Local path to store the pulled vault (defaults to profile's registered path).",
)
def pull_cmd(profile: str, sync_dir: str, vault_path: str | None):
    """Pull a vault from the shared sync directory."""
    if vault_path is None:
        index = load_index()
        if profile not in index:
            raise click.ClickException(
                f"Profile '{profile}' not registered locally. Provide --vault-path."
            )
        vault_path = index[profile]["vault_path"]

    result = pull(profile, Path(sync_dir), Path(vault_path))
    click.echo(f"Pulled '{profile}' vault to {result}")


@sync_group.command("status")
@click.option(
    "--sync-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Shared directory to inspect.",
)
def status_cmd(sync_dir: str):
    """List all vaults available in the shared sync directory."""
    entries = list_remote(Path(sync_dir))
    if not entries:
        click.echo("No vaults found in sync directory.")
        return
    for name, meta in sorted(entries.items()):
        click.echo(f"  {name:<20} pushed_at={meta.get('pushed_at', 'unknown')}  size={meta.get('size', '?')}B")
