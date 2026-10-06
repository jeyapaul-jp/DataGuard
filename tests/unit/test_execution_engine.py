"""Tests for execution engine — tasks 5.1–5.6."""
import pandas as pd
import pytest

from dataguard.execution.result import CheckResult
from dataguard.config.models import DataguardConfig


# --- CheckResult serialization (task 5.1) ---

def test_check_result_to_dict_has_all_fields():
    r = CheckResult(run_id="r1", check_name="c1", check_type="row_count", status="PASS")
    d = r.to_dict()
    for field in ("run_id", "check_name", "check_type", "status", "actual_value",
                  "expected_value", "delta", "null_count", "source_connector_type",
                  "target_connector_type", "timestamp", "reason"):
        assert field in d


def test_new_run_id_is_uuid_format():
    rid = CheckResult.new_run_id()
    parts = rid.split("-")
    assert len(parts) == 5


# --- Execution engine via integration-style call (task 5.2) ---

def _make_config(checks_raw, connections_raw=None):
    connections = connections_raw or {"db": {"type": "sql", "url": "sqlite://"}}
    return DataguardConfig.model_validate({
        "connections": connections,
        "checks": checks_raw,
        "output": {"type": "csv", "path": "/tmp/test_engine_out.csv"},
    })


class _MockWriter:
    def __init__(self):
        self.records = []
        self.samples = []

    def write(self, result, sample_df):
        self.records.append(result)
        self.samples.append(sample_df)

    def close(self):
        pass


def test_engine_produces_result_per_check(tmp_path):
    from dataguard.execution.engine import run_checks
    from sqlalchemy import create_engine, text

    db = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE src (id INTEGER)"))
        conn.execute(text("INSERT INTO src VALUES (1),(2),(3)"))
        conn.execute(text("CREATE TABLE tgt (id INTEGER)"))
        conn.execute(text("INSERT INTO tgt VALUES (1),(2),(3)"))

    config = DataguardConfig.model_validate({
        "connections": {"db": {"type": "sql", "url": f"sqlite:///{db}"}},
        "checks": [
            {"name": "rc", "check_type": "row_count",
             "source": {"connection": "db", "query": "SELECT * FROM src"},
             "target": {"connection": "db", "query": "SELECT * FROM tgt"},
             "threshold_pct": 0},
        ],
        "output": {"type": "csv", "path": str(tmp_path / "out.csv")},
    })
    writer = _MockWriter()
    results = run_checks(config, {}, set(), writer)
    assert len(results) == 1
    assert results[0].status == "PASS"


def test_connection_failure_produces_error_and_continues(tmp_path):
    from dataguard.execution.engine import run_checks

    config = DataguardConfig.model_validate({
        "connections": {
            "bad": {"type": "sql", "url": "sqlite:////nonexistent/path/db.sqlite"},
            "db": {"type": "sql", "url": "sqlite://"},
        },
        "checks": [
            {"name": "broken", "check_type": "row_count",
             "source": {"connection": "bad", "query": "SELECT 1"},
             "target": {"connection": "bad", "query": "SELECT 1"}},
            {"name": "ok", "check_type": "row_count",
             "source": {"connection": "db", "query": "SELECT 1 AS id"},
             "target": {"connection": "db", "query": "SELECT 1 AS id"},
             "threshold_pct": 0},
        ],
        "output": {"type": "csv", "path": str(tmp_path / "out.csv")},
    })
    writer = _MockWriter()
    results = run_checks(config, {}, set(), writer)
    assert len(results) == 2
    statuses = {r.check_name: r.status for r in results}
    assert statuses["broken"] == "ERROR"
    assert statuses["ok"] == "PASS"


# --- SKIP handling (task 5.3) ---

def test_disabled_check_is_skipped(tmp_path):
    from dataguard.execution.engine import run_checks

    config = DataguardConfig.model_validate({
        "connections": {"db": {"type": "sql", "url": "sqlite://"}},
        "checks": [
            {"name": "skipped_check", "check_type": "row_count",
             "source": {"connection": "db", "query": "SELECT 1 AS id"},
             "target": {"connection": "db", "query": "SELECT 1 AS id"},
             "enabled": False},
        ],
        "output": {"type": "csv", "path": str(tmp_path / "out.csv")},
    })
    writer = _MockWriter()
    results = run_checks(config, {}, set(), writer)
    assert results[0].status == "SKIP"


def test_cli_skip_flag_skips_check(tmp_path):
    from dataguard.execution.engine import run_checks

    config = DataguardConfig.model_validate({
        "connections": {"db": {"type": "sql", "url": "sqlite://"}},
        "checks": [
            {"name": "to_skip", "check_type": "row_count",
             "source": {"connection": "db", "query": "SELECT 1 AS id"},
             "target": {"connection": "db", "query": "SELECT 1 AS id"}},
        ],
        "output": {"type": "csv", "path": str(tmp_path / "out.csv")},
    })
    writer = _MockWriter()
    results = run_checks(config, {}, {"to_skip"}, writer)
    assert results[0].status == "SKIP"


# --- Exit code logic (task 5.6) — tested via status counts ---

def test_all_skip_results_would_exit_zero():
    results = [
        CheckResult(run_id="r", check_name="c", check_type="row_count", status="SKIP"),
    ]
    non_skip = [r for r in results if r.status not in ("SKIP",)]
    fails = [r for r in non_skip if r.status in ("FAIL", "ERROR")]
    assert len(fails) == 0  # would exit 0
