from __future__ import annotations

from typing import Optional
import pandas as pd

from dataguard.config.models import NullThresholdCheckConfig
from dataguard.execution.result import CheckResult


def run_null_threshold(
    config: NullThresholdCheckConfig,
    run_id: str,
    source_df: pd.DataFrame,
    source_connector_type: Optional[str] = None,
) -> tuple[CheckResult, Optional[pd.DataFrame]]:
    """Fail if the null rate in config.column exceeds config.threshold_pct."""
    total = len(source_df)
    null_mask = source_df[config.column].isna()
    null_count = int(null_mask.sum())

    if total == 0:
        null_rate = 0.0
    else:
        null_rate = null_count / total * 100.0

    delta = round(null_rate - config.threshold_pct, 6)
    status = "PASS" if null_rate <= config.threshold_pct else "FAIL"
    sample = source_df[null_mask].head(config.sample_rows).copy() if status == "FAIL" else None

    result = CheckResult(
        run_id=run_id,
        check_name=config.name,
        check_type="null_threshold",
        status=status,
        actual_value=round(null_rate, 6),
        expected_value=config.threshold_pct,
        delta=delta,
        null_count=null_count,
        source_connector_type=source_connector_type,
        reason=None if status == "PASS" else (
            f"null rate {null_rate:.2f}% exceeds threshold {config.threshold_pct}%"
        ),
    )
    return result, sample
