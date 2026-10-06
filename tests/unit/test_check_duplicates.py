"""Tests for Duplicate Detection check — task 4.2."""
import pandas as pd
import pytest

from dataguard.checks.duplicates import run_duplicate_detection
from dataguard.config.models import DuplicateCheckConfig, CheckEndpoint


def _cfg(key_columns=("id",), sample_rows=5):
    return DuplicateCheckConfig(
        name="dup",
        source=CheckEndpoint(connection="src"),
        key_columns=list(key_columns),
        sample_rows=sample_rows,
    )


def test_no_duplicates_passes():
    df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    result, sample = run_duplicate_detection(_cfg(), "rid", df)
    assert result.status == "PASS"
    assert sample is None


def test_duplicates_fails_with_samples():
    df = pd.DataFrame({"id": [1, 1, 2, 3, 3], "val": ["a", "a2", "b", "c", "c2"]})
    result, sample = run_duplicate_detection(_cfg(), "rid", df)
    assert result.status == "FAIL"
    assert result.actual_value == 4  # 4 rows involved in duplicates
    assert sample is not None
    assert len(sample) <= 5


def test_sample_rows_capped_at_actual_count():
    df = pd.DataFrame({"id": [1, 1], "val": ["a", "b"]})  # only 2 dup rows
    result, sample = run_duplicate_detection(_cfg(sample_rows=10), "rid", df)
    assert result.status == "FAIL"
    assert len(sample) == 2  # fewer than N, so capped at actual


def test_custom_sample_rows_respected():
    rows = [{"id": i // 2, "val": i} for i in range(20)]
    df = pd.DataFrame(rows)
    _, sample = run_duplicate_detection(_cfg(sample_rows=3), "rid", df)
    assert len(sample) == 3
