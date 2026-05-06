"""CLI commands for managing vault key pins."""

from __future__ import annotations

import click

from envault.pin import PinError, check_pin, get_pin, pin_key, remove_pin
from envault.profiles import load_index


@click.group("pin")
def pin_group() -> None:
    """Manage key fingerprint pins for profiles."""


@pin_group.command("set")
@click.argument("profile")
@click.option("--key", prompt=True, hide_input=True, help="Master key to pin.")
def set_pin_cmd(profile: str, key: str) -> None:
    """Pin PROFILE to the given master key fingerprint."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile: {profile}", err=True)
        raise SystemExit(1)
    profile_dir = index[profile].parent
    fp = pin_key(profile_dir, key)
    click.echo(f"Pinned profile '{profile}' to key fingerprint: {fp}")


@pin_group.command("check")
@click.argument("profile")
@click.option("--key", prompt=True, hide_input=True, help="Master key to verify.")
def check_pin_cmd(profile: str, key: str) -> None:
    """Check whether KEY matches the stored pin for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile: {profile}", err=True)
        raise SystemExit(1)
    profile_dir = index[profile].parent
    try:
        ok = check_pin(profile_dir, key)
    except PinError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    if ok:
        click.echo("Key matches pin. ✓")
    else:
        click.echo("Key does NOT match pin. ✗", err=True)
        raise SystemExit(1)


@pin_group.command("show")
@click.argument("profile")
def show_pin_cmd(profile: str) -> None:
    """Show the stored fingerprint for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile: {profile}", err=True)
        raise SystemExit(1)
    profile_dir = index[profile].parent
    try:
        fp = get_pin(profile_dir)
    except PinError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    if fp is None:
        click.echo(f"Profile '{profile}' is not pinned.")
    else:
        click.echo(f"Fingerprint: {fp}")


@pin_group.command("remove")
@click.argument("profile")
def remove_pin_cmd(profile: str) -> None:
    """Remove the key pin for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile: {profile}", err=True)
        raise SystemExit(1)
    profile_dir = index[profile].parent
    removed = remove_pin(profile_dir)
    if removed:
        click.echo(f"Pin removed for profile '{profile}'.")
    else:
        click.echo(f"Profile '{profile}' was not pinned.")
