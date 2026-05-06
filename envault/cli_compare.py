"""CLI commands for comparing vault profiles."""
import click
from pathlib import Path

from envault.compare import compare_profiles, compare_vaults, CompareError, summary_lines


@click.group("compare")
def compare_group() -> None:
    """Compare two vault profiles or vault files."""


@compare_group.command("profiles")
@click.argument("left_profile")
@click.argument("right_profile")
@click.option("--key", envvar="ENVAULT_MASTER_KEY", required=True, help="Master key for decryption.")
@click.option("--base-dir", default=None, type=click.Path(), help="Profiles base directory.")
def compare_profiles_cmd(left_profile: str, right_profile: str, key: str, base_dir: str | None) -> None:
    """Compare two named profiles side-by-side."""
    bd = Path(base_dir) if base_dir else None
    try:
        result = compare_profiles(left_profile, right_profile, key, base_dir=bd)
    except CompareError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Comparing '{left_profile}' vs '{right_profile}':")
    for line in summary_lines(result, left_label=left_profile, right_label=right_profile):
        click.echo(line)

    if result.has_differences:
        raise SystemExit(1)


@compare_group.command("files")
@click.argument("left_vault", type=click.Path(exists=True))
@click.argument("right_vault", type=click.Path(exists=True))
@click.option("--key", envvar="ENVAULT_MASTER_KEY", required=True, help="Master key for decryption.")
@click.option("--left-label", default="left", help="Label for the left vault.")
@click.option("--right-label", default="right", help="Label for the right vault.")
def compare_files_cmd(
    left_vault: str, right_vault: str, key: str, left_label: str, right_label: str
) -> None:
    """Compare two vault files directly."""
    try:
        result = compare_vaults(Path(left_vault), Path(right_vault), key)
    except CompareError as exc:
        raise click.ClickException(str(exc))
    except ValueError as exc:
        raise click.ClickException(f"Decryption failed: {exc}")

    click.echo(f"Comparing '{left_vault}' vs '{right_vault}':")
    for line in summary_lines(result, left_label=left_label, right_label=right_label):
        click.echo(line)

    if result.has_differences:
        raise SystemExit(1)
