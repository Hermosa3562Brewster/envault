"""CLI commands for managing per-profile secret quotas."""
from __future__ import annotations

import click

from envault.profiles import load_index
from envault.quota import (
    QuotaError,
    effective_limit,
    load_quota,
    remove_override,
    set_limit,
)
from pathlib import Path


@click.group("quota")
def quota_group() -> None:
    """Manage secret quota limits for profiles."""


@quota_group.command("set")
@click.argument("profile")
@click.argument("limit", type=int)
@click.option("--key", default=None, help="Apply limit to a specific key only.")
def set_cmd(profile: str, limit: int, key: str | None) -> None:
    """Set the quota LIMIT for PROFILE (optionally scoped to --key)."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]["path"]).parent
    try:
        set_limit(profile_dir, limit, key=key)
    except QuotaError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    scope = f" (key={key})" if key else ""
    click.echo(f"Quota for '{profile}'{scope} set to {limit}.")


@quota_group.command("show")
@click.argument("profile")
def show_cmd(profile: str) -> None:
    """Show current quota settings for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]["path"]).parent
    try:
        record = load_quota(profile_dir)
    except QuotaError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    click.echo(f"Global limit : {record.limit}")
    if record.overrides:
        click.echo("Per-key overrides:")
        for k, v in sorted(record.overrides.items()):
            click.echo(f"  {k}: {v}")
    else:
        click.echo("No per-key overrides.")


@quota_group.command("remove-override")
@click.argument("profile")
@click.argument("key")
def remove_override_cmd(profile: str, key: str) -> None:
    """Remove a per-key quota override for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]["path"]).parent
    try:
        remove_override(profile_dir, key)
    except QuotaError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    click.echo(f"Removed override for '{key}' in profile '{profile}'.")
