"""CLI commands for managing profile policies in envault."""
from __future__ import annotations

from pathlib import Path

import click

from envault.policy import PolicyError, add_rule, enforce, load_policy, remove_rule
from envault.profiles import load_index
from envault.vault import load_vault


@click.group("policy")
def policy_group() -> None:
    """Manage key policies for a profile."""


@policy_group.command("add")
@click.argument("profile")
@click.option("--kind", type=click.Choice(["require", "forbid"]), required=True,
              help="Rule type: 'require' a matching key or 'forbid' matching keys.")
@click.option("--pattern", required=True, help="Regex pattern matched against key names.")
@click.option("--reason", default="", help="Human-readable explanation for this rule.")
def add_rule_cmd(profile: str, kind: str, pattern: str, reason: str) -> None:
    """Add a policy rule to PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]).parent
    try:
        add_rule(profile_dir, kind, pattern, reason)
        click.echo(f"Added {kind} rule for pattern '{pattern}' to profile '{profile}'.")
    except PolicyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@policy_group.command("remove")
@click.argument("profile")
@click.option("--pattern", required=True, help="Exact pattern string to remove.")
def remove_rule_cmd(profile: str, pattern: str) -> None:
    """Remove a policy rule from PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]).parent
    try:
        removed = remove_rule(profile_dir, pattern)
        if removed:
            click.echo(f"Removed rule '{pattern}' from profile '{profile}'.")
        else:
            click.echo(f"No rule with pattern '{pattern}' found.", err=True)
            raise SystemExit(1)
    except PolicyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@policy_group.command("list")
@click.argument("profile")
def list_cmd(profile: str) -> None:
    """List all policy rules for PROFILE."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    profile_dir = Path(index[profile]).parent
    rules = load_policy(profile_dir)
    if not rules:
        click.echo("No policy rules defined.")
        return
    for rule in rules:
        line = f"[{rule.kind}] {rule.pattern}"
        if rule.reason:
            line += f"  # {rule.reason}"
        click.echo(line)


@policy_group.command("check")
@click.argument("profile")
@click.option("--key", required=True, help="Master key to decrypt the vault.")
def check_cmd(profile: str, key: str) -> None:
    """Check vault contents of PROFILE against its policy."""
    index = load_index()
    if profile not in index:
        click.echo(f"Unknown profile '{profile}'.", err=True)
        raise SystemExit(1)
    vault_path = Path(index[profile])
    profile_dir = vault_path.parent
    try:
        env = load_vault(vault_path, key)
    except Exception as exc:
        click.echo(f"Failed to load vault: {exc}", err=True)
        raise SystemExit(1)
    rules = load_policy(profile_dir)
    result = enforce(env, rules)
    if result.passed:
        click.echo("Policy check passed. No violations.")
    else:
        click.echo("Policy violations found:", err=True)
        for v in result.violations:
            click.echo(f"  - {v}", err=True)
        raise SystemExit(1)
