"""File connector integration tests — task 7.2."""
import textwrap

import pandas as pd
import pytest
from click.testing import CliRunner

from dataguard.cli import main


@pytest.fixture()
def file_fixtures(tmp_path):
    src_csv = tmp_path / "source.csv"
    tgt_parquet = tmp_path / "target.parquet"

    src_df = pd.DataFrame({"id": range(10), "amount": [float(i * 10) for i in range(10)],
                            "notes": ["ok"] * 9 + [None]})
    src_df.to_csv(src_csv, index=False)

    tgt_df = pd.DataFrame({"id": range(8), "amount": [float(i * 10) for i in range(8)]})
    tgt_df.to_parquet(tgt_parquet, index=False)

    return {"src_csv": src_csv, "tgt_parquet": tgt_parquet, "tmp": tmp_path}


@pytest.fixture()
def file_config(file_fixtures, tmp_path):
    src = file_fixtures["src_csv"]
    tgt = file_fixtures["tgt_parquet"]
    results_csv = tmp_path / "results.csv"

    body = textwrap.dedent(f"""
        connections:
          src_csv:
            type: csv
            path: "{src}"
          tgt_parquet:
            type: parquet
            path: "{tgt}"

        checks:
          - name: row_count_csv_vs_parquet
            check_type: row_count
            source:
              connection: src_csv
            target:
              connection: tgt_parquet
            threshold_pct: 1.0

          - name: null_notes
            check_type: null_threshold
            source:
              connection: src_csv
            column: notes
            threshold_pct: 5.0

        output:
          type: csv
          path: "{results_csv}"
    """)
    cfg_file = tmp_path / "file_config.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    return cfg_file, results_csv


def test_file_connectors_run_and_write_results(file_config):
    cfg_file, results_csv = file_config
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--config", str(cfg_file)])
    assert results_csv.exists()
    df = pd.read_csv(results_csv)
    assert len(df) == 2
    assert set(df.columns) >= {"run_id", "check_name", "status"}


def test_file_results_store_appends_across_runs(file_config):
    cfg_file, results_csv = file_config
    runner = CliRunner()
    runner.invoke(main, ["run", "--config", str(cfg_file)])
    runner.invoke(main, ["run", "--config", str(cfg_file)])
    df = pd.read_csv(results_csv)
    assert len(df) == 4  # 2 checks × 2 runs
