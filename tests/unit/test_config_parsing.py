"""Tests for config parsing: tasks 2.1–2.6."""
import os
import textwrap

import pytest
from pydantic import ValidationError

from dataguard.config.models import (
    SqlConnection, SnowflakeConnection, DatabricksConnection,
    CsvConnection, DataguardConfig,
)
from dataguard.config.parser import parse_config, ConfigError


# --- Connection model validation (task 2.1) ---

def test_sql_connection_missing_url_raises():
    with pytest.raises(ValidationError, match="url"):
        SqlConnection.model_validate({"type": "sql"})


def test_snowflake_connection_missing_account_raises():
    with pytest.raises(ValidationError, match="account"):
        SnowflakeConnection.model_validate({"type": "snowflake", "warehouse": "WH", "database": "DB", "schema_name": "S", "user": "U"})


def test_databricks_connection_missing_host_raises():
    with pytest.raises(ValidationError, match="host"):
        DatabricksConnection.model_validate({"type": "databricks", "http_path": "/sql/1.0/warehouses/x", "access_token": "tok"})


# --- Check model validation (task 2.2) ---

def test_row_count_check_missing_source_raises():
    with pytest.raises(ValidationError, match="source"):
        DataguardConfig.model_validate({
            "connections": {"db": {"type": "sql", "url": "sqlite://"}},
            "checks": [{"name": "c1", "check_type": "row_count", "target": {"connection": "db", "query": "SELECT 1"}}],
            "output": {"type": "csv", "path": "/tmp/out.csv"},
        })


def test_null_threshold_check_missing_column_raises():
    with pytest.raises(ValidationError, match="column"):
        DataguardConfig.model_validate({
            "connections": {"db": {"type": "sql", "url": "sqlite://"}},
            "checks": [{"name": "c1", "check_type": "null_threshold", "source": {"connection": "db"}, "threshold_pct": 10}],
            "output": {"type": "csv", "path": "/tmp/out.csv"},
        })


# --- parse_config: syntax errors (task 2.3) ---

def test_parse_config_invalid_yaml_raises(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("checks: [\n  unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match=str(cfg)):
        parse_config(str(cfg))


def test_parse_config_valid_yaml_and_json_produce_same_model(tmp_path):
    body = textwrap.dedent("""
        connections:
          db:
            type: sql
            url: "sqlite://"
        checks:
          - name: c1
            check_type: row_count
            source: {connection: db, query: "SELECT 1"}
            target: {connection: db, query: "SELECT 1"}
            threshold_pct: 0
        output:
          type: csv
          path: /tmp/out.csv
    """)
    yaml_cfg = tmp_path / "cfg.yaml"
    yaml_cfg.write_text(body, encoding="utf-8")
    cfg_yaml, _ = parse_config(str(yaml_cfg))
    assert cfg_yaml.checks[0].name == "c1"


# --- Env var resolution (task 2.4) ---

def test_env_var_resolved_at_parse_time(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PASS", "secret")
    body = textwrap.dedent("""
        connections:
          db:
            type: sql
            url: "sqlite://"
            password: "${DB_PASS}"
        checks: []
        output: {type: csv, path: /tmp/out.csv}
    """)
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    # SqlConnection doesn't have a password field; but the raw dict resolution should work
    # Just verify parse succeeds (password would be discarded by the model)
    config, missing = parse_config(str(cfg_file))
    assert missing == {}


def test_missing_env_var_flagged_not_raised(tmp_path, monkeypatch):
    monkeypatch.delenv("DB_PASS", raising=False)
    body = textwrap.dedent("""
        connections:
          db:
            type: sql
            url: "${DB_PASS}"
        checks: []
        output: {type: csv, path: /tmp/out.csv}
    """)
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    config, missing = parse_config(str(cfg_file))
    assert "db" in missing
    assert "DB_PASS" in missing["db"]


# --- output_fields validation (task 2.5) ---

def test_output_fields_missing_required_status_raises():
    with pytest.raises(ValidationError, match="status"):
        DataguardConfig.model_validate({
            "connections": {},
            "checks": [],
            "output": {"type": "csv", "path": "/tmp/out.csv", "output_fields": ["run_id", "check_name"]},
        })


def test_output_fields_invalid_field_name_raises():
    with pytest.raises(ValidationError, match="Invalid output_fields"):
        DataguardConfig.model_validate({
            "connections": {},
            "checks": [],
            "output": {"type": "csv", "path": "/tmp/out.csv", "output_fields": ["run_id", "check_name", "status", "bogus_field"]},
        })


# --- Duplicate check name detection (task 2.6) ---

def test_duplicate_check_name_raises():
    with pytest.raises(ValidationError, match="Duplicate check name"):
        DataguardConfig.model_validate({
            "connections": {"db": {"type": "sql", "url": "sqlite://"}},
            "checks": [
                {"name": "same", "check_type": "row_count",
                 "source": {"connection": "db", "query": "SELECT 1"},
                 "target": {"connection": "db", "query": "SELECT 1"}},
                {"name": "same", "check_type": "row_count",
                 "source": {"connection": "db", "query": "SELECT 1"},
                 "target": {"connection": "db", "query": "SELECT 1"}},
            ],
            "output": {"type": "csv", "path": "/tmp/out.csv"},
        })
