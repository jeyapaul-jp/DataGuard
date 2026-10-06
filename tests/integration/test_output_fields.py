"""output_fields projection end-to-end tests — task 7.4."""
import textwrap

import pandas as pd
import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from dataguard.cli import main
from dataguard.config.models import DataguardConfig


@pytest.fixture()
def projected_config(tmp_path):
    results_csv = tmp_path / "results_projected.csv"
    body = textwrap.dedent(f"""
        connections:
          db:
            type: sql
            url: "sqlite://"

        checks:
          - name: rc
            check_type: row_count
            source: {{connection: db, query: "SELECT 1 AS id"}}
            target: {{connection: db, query: "SELECT 1 AS id"}}
            threshold_pct: 0

        output:
          type: csv
          path: "{results_csv}"
          output_fields: [run_id, check_name, status, timestamp]
    """)
    cfg_file = tmp_path / "projected.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    return cfg_file, results_csv


def test_output_fields_projection_produces_exact_columns(projected_config):
    cfg_file, results_csv = projected_config
    runner = CliRunner()
    runner.invoke(main, ["run", "--config", str(cfg_file)])
    df = pd.read_csv(results_csv)
    assert list(df.columns) == ["run_id", "check_name", "status", "timestamp"]


def test_config_omitting_status_is_rejected():
    with pytest.raises(ValidationError, match="status"):
        DataguardConfig.model_validate({
            "connections": {},
            "checks": [],
            "output": {
                "type": "csv",
                "path": "/tmp/out.csv",
                "output_fields": ["run_id", "check_name"],  # missing "status"
            },
        })
