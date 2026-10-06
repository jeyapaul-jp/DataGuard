"""Tests for Referential Integrity check — task 4.4."""
import pandas as pd
import pytest

from dataguard.checks.referential_integrity import run_referential_integrity
from dataguard.config.models import ReferentialIntegrityCheckConfig, CheckEndpoint


def _cfg(sample_rows=5):
    return ReferentialIntegrityCheckConfig(
        name="ri",
        source=CheckEndpoint(connection="src"),
        source_column="category_id",
        target=CheckEndpoint(connection="tgt"),
        target_column="id",
        sample_rows=sample_rows,
    )


def test_all_values_present_passes():
    src = pd.DataFrame({"category_id": [1, 2, 3]})
    tgt = pd.DataFrame({"id": [1, 2, 3, 4]})
    result, sample = run_referential_integrity(_cfg(), "rid", src, tgt)
    assert result.status == "PASS"
    assert sample is None


def test_orphaned_values_fail_with_samples():
    src = pd.DataFrame({"category_id": [1, 2, 99]})
    tgt = pd.DataFrame({"id": [1, 2, 3]})
    result, sample = run_referential_integrity(_cfg(), "rid", src, tgt)
    assert result.status == "FAIL"
    assert result.actual_value == 1  # 1 orphaned
    assert sample is not None
    assert len(sample) == 1


def test_null_source_values_excluded_and_counted():
    src = pd.DataFrame({"category_id": [1, None, 99]})
    tgt = pd.DataFrame({"id": [1, 2]})
    result, sample = run_referential_integrity(_cfg(), "rid", src, tgt)
    assert result.status == "FAIL"
    assert result.null_count == 1
    assert result.actual_value == 1  # 99 is orphaned; NULL is excluded


def test_sample_count_capped():
    src = pd.DataFrame({"category_id": [10, 11, 12]})
    tgt = pd.DataFrame({"id": [1, 2]})
    _, sample = run_referential_integrity(_cfg(sample_rows=2), "rid", src, tgt)
    assert sample is not None
    assert len(sample) == 2
