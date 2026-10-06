"""Tests for Reconciliation check — task 4.5."""
import pandas as pd
import pytest

from dataguard.checks.reconciliation import run_reconciliation
from dataguard.config.models import ReconciliationCheckConfig, CheckEndpoint


def _cfg(aggregate="sum", threshold_pct=0.1):
    return ReconciliationCheckConfig(
        name="recon",
        source=CheckEndpoint(connection="src"),
        source_column="amount",
        target=CheckEndpoint(connection="tgt"),
        target_column="amount",
        aggregate=aggregate,
        threshold_pct=threshold_pct,
    )


def test_sum_within_threshold_passes():
    src = pd.DataFrame({"amount": [100.0, 200.0, 300.0]})
    tgt = pd.DataFrame({"amount": [100.0, 200.0, 299.8]})
    result, _ = run_reconciliation(_cfg("sum", 0.1), "rid", src, tgt)
    assert result.status == "PASS"


def test_sum_exceeds_threshold_fails():
    src = pd.DataFrame({"amount": [1_000_000.0]})
    tgt = pd.DataFrame({"amount": [990_000.0]})
    result, _ = run_reconciliation(_cfg("sum", 0.1), "rid", src, tgt)
    assert result.status == "FAIL"
    assert result.delta == pytest.approx(1.0)


def test_count_aggregate():
    src = pd.DataFrame({"amount": [1, 2, None, 4]})  # 3 non-null
    tgt = pd.DataFrame({"amount": [1, 2, 3, 4]})     # 4 non-null
    result, _ = run_reconciliation(_cfg("count", 10.0), "rid", src, tgt)
    assert result.status == "FAIL"
    assert result.actual_value == pytest.approx(3.0)


def test_avg_aggregate():
    src = pd.DataFrame({"amount": [10.0, 20.0]})
    tgt = pd.DataFrame({"amount": [10.0, 20.0]})
    result, _ = run_reconciliation(_cfg("avg", 0.0), "rid", src, tgt)
    assert result.status == "PASS"


def test_null_columns_reported():
    src = pd.DataFrame({"amount": [1.0, None, 3.0]})
    tgt = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})
    result, _ = run_reconciliation(_cfg("sum", 50.0), "rid", src, tgt)
    assert result.null_count == 1  # 1 null in source


def test_no_sample_rows_produced_on_fail():
    src = pd.DataFrame({"amount": [1_000_000.0]})
    tgt = pd.DataFrame({"amount": [1.0]})
    _, sample = run_reconciliation(_cfg("sum", 0.1), "rid", src, tgt)
    assert sample is None
