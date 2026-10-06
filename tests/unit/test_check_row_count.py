"""Tests for Row Count check — task 4.1."""
import pandas as pd
import pytest

from dataguard.checks.row_count import run_row_count
from dataguard.config.models import RowCountCheckConfig, CheckEndpoint


def _cfg(threshold_pct=1.0):
    return RowCountCheckConfig(
        name="rc",
        source=CheckEndpoint(connection="src"),
        target=CheckEndpoint(connection="tgt"),
        threshold_pct=threshold_pct,
    )


def _df(n):
    return pd.DataFrame({"id": range(n)})


def test_within_threshold_passes():
    result, sample = run_row_count(_cfg(1.0), "rid", _df(1000), _df(998))
    assert result.status == "PASS"
    assert sample is None


def test_exceeds_threshold_fails():
    result, sample = run_row_count(_cfg(1.0), "rid", _df(1000), _df(950))
    assert result.status == "FAIL"
    assert sample is None
    assert result.actual_value == 1000
    assert result.expected_value == 950
    assert result.delta == pytest.approx(5.0, abs=0.01)


def test_zero_vs_zero_passes():
    result, _ = run_row_count(_cfg(0.0), "rid", _df(0), _df(0))
    assert result.status == "PASS"
    assert result.delta == 0.0


def test_zero_source_vs_nonzero_target_fails():
    result, _ = run_row_count(_cfg(1.0), "rid", _df(0), _df(100))
    assert result.status == "FAIL"
    assert result.delta == pytest.approx(100.0)


def test_zero_target_vs_nonzero_source_fails():
    result, _ = run_row_count(_cfg(1.0), "rid", _df(100), _df(0))
    assert result.status == "FAIL"
    assert result.delta == pytest.approx(100.0)


def test_result_fields_populated():
    result, _ = run_row_count(_cfg(), "rid", _df(1000), _df(990))
    assert result.run_id == "rid"
    assert result.check_name == "rc"
    assert result.check_type == "row_count"
    assert result.timestamp  # non-empty
