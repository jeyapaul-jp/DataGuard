"""CLI --skip integration tests — task 7.3."""
import textwrap

import pandas as pd
import pytest
from click.testing import CliRunner

from dataguard.cli import main


@pytest.fixture()
def skip_config(tmp_path):
    results_csv = tmp_path / "results.csv"
    body = textwrap.dedent(f"""
        connections:
          db:
            type: sql
            url: "sqlite://"

        checks:
          - name: check_a
            check_type: row_count
            source: {{connection: db, query: "SELECT 1 AS id"}}
            target: {{connection: db, query: "SELECT 1 AS id"}}
            threshold_pct: 0

          - name: check_b
            check_type: row_count
            source: {{connection: db, query: "SELECT 1 AS id"}}
            target: {{connection: db, query: "SELECT 1 AS id"}}
            threshold_pct: 0

          - name: check_c
            check_type: row_count
            source: {{connection: db, query: "SELECT 1 AS id"}}
            target: {{connection: db, query: "SELECT 1 AS id"}}
            threshold_pct: 0

        output:
          type: csv
          path: "{results_csv}"
    """)
    cfg_file = tmp_path / "skip_config.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    return cfg_file, results_csv


def test_skip_flag_produces_skip_record(skip_config):
    cfg_file, results_csv = skip_config
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--config", str(cfg_file), "--skip", "check_b"])
    assert result.exit_code == 0
    df = pd.read_csv(results_csv)
    assert len(df) == 3
    skipped = df[df["check_name"] == "check_b"]
    assert skipped.iloc[0]["status"] == "SKIP"


def test_multiple_skip_flags(skip_config):
    cfg_file, results_csv = skip_config
    runner = CliRunner()
    runner.invoke(main, ["run", "--config", str(cfg_file), "--skip", "check_a", "--skip", "check_c"])
    df = pd.read_csv(results_csv)
    statuses = dict(zip(df["check_name"], df["status"]))
    assert statuses["check_a"] == "SKIP"
    assert statuses["check_c"] == "SKIP"
    assert statuses["check_b"] == "PASS"


def test_unknown_skip_name_prints_warning_and_completes(skip_config):
    cfg_file, results_csv = skip_config
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--config", str(cfg_file), "--skip", "nonexistent_check"])
    assert result.exit_code == 0
    assert "Warning" in result.output or "warning" in result.output.lower()
    df = pd.read_csv(results_csv)
    assert len(df) == 3  # all 3 ran
