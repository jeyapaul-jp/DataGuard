"""Tests for Null Threshold check — task 4.3."""
import pandas as pd
import pytest

from dataguard.checks.null_threshold import run_null_threshold
from dataguard.config.models import NullThresholdCheckConfig, CheckEndpoint


def _cfg(threshold_pct=10.0, sample_rows=5):
    return NullThresholdCheckConfig(
        name="null_chk",
        source=CheckEndpoint(connection="src"),
        column="amount",
        threshold_pct=threshold_pct,
        sample_rows=sample_rows,
    )


def _df_with_nulls(n_total, n_null):
    values = [None] * n_null + [1.0] * (n_total - n_null)
    return pd.DataFrame({"amount": values})


def test_below_threshold_passes():
    result, sample = run_null_threshold(_cfg(10.0), "rid", _df_with_nulls(100, 8))
    assert result.status == "PASS"
    assert sample is None


def test_above_threshold_fails_with_samples():
    result, sample = run_null_threshold(_cfg(10.0), "rid", _df_with_nulls(100, 15))
    assert result.status == "FAIL"
    assert sample is not None
    assert len(sample) <= 5
    assert result.actual_value == pytest.approx(15.0)
    assert result.delta == pytest.approx(5.0)


def test_all_null_fails():
    result, sample = run_null_threshold(_cfg(10.0), "rid", _df_with_nulls(10, 10))
    assert result.status == "FAIL"
    assert result.actual_value == pytest.approx(100.0)
    assert result.null_count == 10


def test_empty_dataframe_passes():
    result, _ = run_null_threshold(_cfg(10.0), "rid", pd.DataFrame({"amount": pd.Series([], dtype=float)}))
    assert result.status == "PASS"
    assert result.actual_value == 0.0
