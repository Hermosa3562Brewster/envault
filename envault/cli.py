"""Command-line interface for envault."""

import sys
import click
from pathlib import Path

from envault.vault import lock, unlock, load_vault, save_vault


@click.group()
@click.version_option(prog_name="envault")
def cli():
    """envault — local secrets manager for encrypted .env files."""
    pass


@cli.command("lock")
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    default=".env.vault",
    help="Output path for the encrypted vault file.",
    show_default=True,
)
@click.option("--key", envvar="ENVAULT_MASTER_KEY", prompt=True, hide_input=True,
              help="Master key (or set ENVAULT_MASTER_KEY env var).")
def lock_cmd(env_file, output, key):
    """Encrypt ENV_FILE and write to an encrypted vault."""
    env_path = Path(env_file)
    out_path = Path(output)

    raw = env_path.read_text(encoding="utf-8")
    vault_data = lock(raw, key)
    save_vault(vault_data, out_path)

    click.echo(f"Locked '{env_path}' → '{out_path}'")


@cli.command("unlock")
@click.argument("vault_file", default=".env.vault", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    default=".env",
    help="Output path for the decrypted .env file.",
    show_default=True,
)
@click.option("--key", envvar="ENVAULT_MASTER_KEY", prompt=True, hide_input=True,
              help="Master key (or set ENVAULT_MASTER_KEY env var).")
def unlock_cmd(vault_file, output, key):
    """Decrypt a vault file and write the plaintext .env."""
    vault_path = Path(vault_file)
    out_path = Path(output)

    try:
        vault_data = load_vault(vault_path)
        plaintext = unlock(vault_data, key)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    out_path.write_text(plaintext, encoding="utf-8")
    click.echo(f"Unlocked '{vault_path}' → '{out_path}'")


@cli.command("view")
@click.argument("vault_file", default=".env.vault", type=click.Path(exists=True))
@click.option("--key", envvar="ENVAULT_MASTER_KEY", prompt=True, hide_input=True,
              help="Master key (or set ENVAULT_MASTER_KEY env var).")
def view_cmd(vault_file, key):
    """Print decrypted secrets to stdout without writing a file."""
    vault_path = Path(vault_file)

    try:
        vault_data = load_vault(vault_path)
        plaintext = unlock(vault_data, key)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(plaintext)


if __name__ == "__main__":  # pragma: no cover
    cli()
