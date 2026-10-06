import sys
import click
from dataguard.config import parse_config, ConfigError


@click.group()
def main():
    """DataGuard — config-driven data validation framework for ETL pipelines."""


@main.command()
@click.option("--config", "config_path", required=True, type=click.Path(exists=True), help="Path to YAML or JSON config file.")
@click.option("--skip", multiple=True, help="Skip a check by name. Repeatable: --skip A --skip B.")
def run(config_path: str, skip: tuple):
    """Execute all checks defined in CONFIG."""
    from dataguard.execution import run_checks
    from dataguard.results import FileWriter, DatabaseWriter
    from dataguard.config.models import FileOutputConfig, DatabaseOutputConfig

    try:
        config, missing_env_vars = parse_config(config_path)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not config.checks:
        click.echo("No checks defined — nothing to run.")
        sys.exit(0)

    skip_set = set(skip)
    known_names = {c.name for c in config.checks}
    for name in skip_set:
        if name not in known_names:
            click.echo(f"Warning: --skip '{name}' does not match any check in the config.", err=True)

    output_cfg = config.output
    try:
        if isinstance(output_cfg, FileOutputConfig):
            writer = FileWriter(output_cfg)
        else:
            writer = DatabaseWriter(output_cfg, config.connections)
    except Exception as e:
        click.echo(f"Error initialising Results Store: {e}", err=True)
        sys.exit(1)

    results = run_checks(config, missing_env_vars, skip_set, writer)

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
    for result in results:
        click.echo(f"  [{result.status}] {result.check_name}")
        counts[result.status] = counts.get(result.status, 0) + 1

    writer.close()

    store_path = getattr(output_cfg, "path", None) or getattr(output_cfg, "table", "db-table")
    click.echo(
        f"\nPASS: {counts['PASS']}  FAIL: {counts['FAIL']}  "
        f"SKIP: {counts['SKIP']}  ERROR: {counts['ERROR']}"
    )
    click.echo(f"Results Store: {store_path}")

    if counts["FAIL"] > 0 or counts["ERROR"] > 0:
        sys.exit(1)
    sys.exit(0)
