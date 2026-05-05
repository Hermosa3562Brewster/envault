"""CLI commands for searching across vault profiles."""

from __future__ import annotations

import click

from envault.search import SearchError, search_key, search_value


@click.group("search")
def search_group() -> None:
    """Search for keys or values across vault profiles."""


@search_group.command("key")
@click.argument("pattern")
@click.option("--master-key", envvar="ENVAULT_MASTER_KEY", required=True, help="Master decryption key.")
@click.option("--profile", default=None, help="Limit search to a single profile.")
@click.option("--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive matching.")
def search_key_cmd(pattern: str, master_key: str, profile: str | None, case_sensitive: bool) -> None:
    """Search for PATTERN in env variable names."""
    try:
        result = search_key(
            master_key,
            pattern,
            profile=profile,
            case_sensitive=case_sensitive,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc))

    if not result.has_matches:
        click.echo("No matches found.")
        return

    for prof, matches in result.by_profile().items():
        click.echo(f"[{prof}]")
        for m in matches:
            click.echo(f"  {m.key}")


@search_group.command("value")
@click.argument("pattern")
@click.option("--master-key", envvar="ENVAULT_MASTER_KEY", required=True, help="Master decryption key.")
@click.option("--profile", default=None, help="Limit search to a single profile.")
@click.option("--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive matching.")
@click.option("--show-values", is_flag=True, default=False, help="Print matched values alongside keys.")
def search_value_cmd(
    pattern: str,
    master_key: str,
    profile: str | None,
    case_sensitive: bool,
    show_values: bool,
) -> None:
    """Search for PATTERN in env variable values."""
    try:
        result = search_value(
            master_key,
            pattern,
            profile=profile,
            case_sensitive=case_sensitive,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc))

    if not result.has_matches:
        click.echo("No matches found.")
        return

    for prof, matches in result.by_profile().items():
        click.echo(f"[{prof}]")
        for m in matches:
            if show_values:
                click.echo(f"  {m.key}={m.value}")
            else:
                click.echo(f"  {m.key}")
