"""End-to-end integration test using SQLite — task 7.1."""
import textwrap

import pandas as pd
import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine, text

from dataguard.cli import main


@pytest.fixture()
def sqlite_dbs(tmp_path):
    """Create source and target SQLite databases with test data."""
    src_db = tmp_path / "source.db"
    tgt_db = tmp_path / "target.db"
    results_db = tmp_path / "results.db"

    src_engine = create_engine(f"sqlite:///{src_db}")
    tgt_engine = create_engine(f"sqlite:///{tgt_db}")

    with src_engine.begin() as conn:
        conn.execute(text("CREATE TABLE orders (id INTEGER, amount REAL, category_id INTEGER)"))
        for i in range(10):
            conn.execute(text(f"INSERT INTO orders VALUES ({i}, {i*10.0}, {i % 3 + 1})"))

    with tgt_engine.begin() as conn:
        conn.execute(text("CREATE TABLE orders (id INTEGER, amount REAL, category_id INTEGER)"))
        for i in range(9):  # 1 row missing — Row Count will FAIL
            conn.execute(text(f"INSERT INTO orders VALUES ({i}, {i*10.0}, {i % 3 + 1})"))
        conn.execute(text("CREATE TABLE categories (id INTEGER)"))
        for cid in [1, 2, 3]:
            conn.execute(text(f"INSERT INTO categories VALUES ({cid})"))

    return {"src": src_db, "tgt": tgt_db, "results": results_db, "tmp": tmp_path}


@pytest.fixture()
def config_file(sqlite_dbs, tmp_path):
    src = sqlite_dbs["src"]
    tgt = sqlite_dbs["tgt"]
    results = sqlite_dbs["results"]

    body = textwrap.dedent(f"""
        connections:
          src:
            type: sql
            url: "sqlite:///{src}"
          tgt:
            type: sql
            url: "sqlite:///{tgt}"
          results_db:
            type: sql
            url: "sqlite:///{results}"
          bad_conn:
            type: sql
            url: "sqlite:////nonexistent/totally/fake/db.sqlite"

        checks:
          - name: row_count_orders
            check_type: row_count
            source:
              connection: src
              query: "SELECT * FROM orders"
            target:
              connection: tgt
              query: "SELECT * FROM orders"
            threshold_pct: 1.0

          - name: duplicate_ids
            check_type: duplicate
            source:
              connection: src
              query: "SELECT * FROM orders"
            key_columns: [id]

          - name: null_amounts
            check_type: null_threshold
            source:
              connection: src
              query: "SELECT * FROM orders"
            column: amount
            threshold_pct: 5.0

          - name: ref_integrity_categories
            check_type: referential_integrity
            source:
              connection: src
              query: "SELECT * FROM orders"
            source_column: category_id
            target:
              connection: tgt
              query: "SELECT * FROM categories"
            target_column: id

          - name: reconcile_amounts
            check_type: reconciliation
            source:
              connection: src
              query: "SELECT * FROM orders"
            source_column: amount
            target:
              connection: tgt
              query: "SELECT * FROM orders"
            target_column: amount
            aggregate: sum
            threshold_pct: 20.0

          - name: broken_check
            check_type: row_count
            source:
              connection: bad_conn
              query: "SELECT 1"
            target:
              connection: bad_conn
              query: "SELECT 1"

          - name: intentionally_skipped
            check_type: row_count
            source:
              connection: src
              query: "SELECT 1 AS id"
            target:
              connection: tgt
              query: "SELECT 1 AS id"
            enabled: false

        output:
          type: database
          connection: results_db
          table: check_results
    """)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(body, encoding="utf-8")
    return cfg_file


def test_e2e_sqlite_run(config_file, sqlite_dbs):
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--config", str(config_file)])
    assert result.exit_code == 1, result.output  # FAIL or ERROR present

    results_db = sqlite_dbs["results"]
    engine = create_engine(f"sqlite:///{results_db}")
    df = pd.read_sql("SELECT * FROM check_results", engine)

    assert len(df) == 7
    statuses = dict(zip(df["check_name"], df["status"]))
    assert statuses["intentionally_skipped"] == "SKIP"
    assert statuses["broken_check"] == "ERROR"
    assert statuses["duplicate_ids"] == "PASS"
    assert statuses["null_amounts"] == "PASS"
    assert statuses["ref_integrity_categories"] == "PASS"
