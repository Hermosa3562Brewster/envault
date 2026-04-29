"""CLI commands for vault snapshot management."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.profiles import load_index
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


@click.group("snapshot", help="Manage named vault snapshots.")
def snapshot_group() -> None:
    pass


@snapshot_group.command("create")
@click.argument("profile")
@click.argument("name")
def create_cmd(profile: str, name: str) -> None:
    """Create a snapshot NAME for PROFILE's vault."""
    profiles = load_index()
    if profile not in profiles:
        click.echo(f"Unknown profile: {profile}", err=True)
        sys.exit(1)

    vault_path = Path(profiles[profile]["vault_path"])
    try:
        snap = create_snapshot(vault_path, name)
        click.echo(f"Snapshot '{name}' created: {snap}")
    except SnapshotError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)


@snapshot_group.command("restore")
@click.argument("profile")
@click.argument("name")
def restore_cmd(profile: str, name: str) -> None:
    """Restore vault to snapshot NAME for PROFILE."""
    profiles = load_index()
    if profile not in profiles:
        click.echo(f"Unknown profile: {profile}", err=True)
        sys.exit(1)

    vault_path = Path(profiles[profile]["vault_path"])
    try:
        restore_snapshot(vault_path, name)
        click.echo(f"Vault restored to snapshot '{name}'.")
    except SnapshotError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)


@snapshot_group.command("list")
@click.argument("profile")
def list_cmd(profile: str) -> None:
    """List all snapshots for PROFILE."""
    profiles = load_index()
    if profile not in profiles:
        click.echo(f"Unknown profile: {profile}", err=True)
        sys.exit(1)

    vault_path = Path(profiles[profile]["vault_path"])
    snaps = list_snapshots(vault_path)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        click.echo(f"  {s['name']:20s}  {s['created_at']}")


@snapshot_group.command("delete")
@click.argument("profile")
@click.argument("name")
def delete_cmd(profile: str, name: str) -> None:
    """Delete snapshot NAME for PROFILE."""
    profiles = load_index()
    if profile not in profiles:
        click.echo(f"Unknown profile: {profile}", err=True)
        sys.exit(1)

    vault_path = Path(profiles[profile]["vault_path"])
    try:
        delete_snapshot(vault_path, name)
        click.echo(f"Snapshot '{name}' deleted.")
    except SnapshotError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
