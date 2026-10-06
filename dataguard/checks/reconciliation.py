from __future__ import annotations

from typing import Optional
import pandas as pd

from dataguard.config.models import ReconciliationCheckConfig
from dataguard.execution.result import CheckResult


def _aggregate(series: pd.Series, agg: str) -> float:
    s = series.dropna()
    if agg == "sum":
        return float(s.sum())
    if agg == "count":
        return float(len(s))
    if agg == "avg":
        return float(s.mean()) if len(s) > 0 else 0.0
    raise ValueError(f"Unknown aggregate: {agg}")


def run_reconciliation(
    config: ReconciliationCheckConfig,
    run_id: str,
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    source_connector_type: Optional[str] = None,
    target_connector_type: Optional[str] = None,
) -> tuple[CheckResult, None]:
    """Compare aggregate of source vs target column; percentage delta check."""
    src_null_count = int(source_df[config.source_column].isna().sum())
    tgt_null_count = int(target_df[config.target_column].isna().sum())

    src_agg = _aggregate(source_df[config.source_column], config.aggregate)
    tgt_agg = _aggregate(target_df[config.target_column], config.aggregate)

    if src_agg == 0 and tgt_agg == 0:
        delta_pct = 0.0
    elif src_agg == 0:
        delta_pct = 100.0
    else:
        delta_pct = abs(src_agg - tgt_agg) / abs(src_agg) * 100.0

    status = "PASS" if delta_pct <= config.threshold_pct else "FAIL"

    result = CheckResult(
        run_id=run_id,
        check_name=config.name,
        check_type="reconciliation",
        status=status,
        actual_value=src_agg,
        expected_value=tgt_agg,
        delta=round(delta_pct, 6),
        null_count=src_null_count + tgt_null_count,
        source_connector_type=source_connector_type,
        target_connector_type=target_connector_type,
        reason=None if status == "PASS" else (
            f"{config.aggregate} delta {delta_pct:.4f}% exceeds threshold {config.threshold_pct}% "
            f"(src_nulls={src_null_count}, tgt_nulls={tgt_null_count})"
        ),
    )
    return result, None  # Reconciliation never produces sample rows
