from __future__ import annotations

from typing import Optional
import pandas as pd

from dataguard.config.models import RowCountCheckConfig
from dataguard.execution.result import CheckResult


def run_row_count(
    config: RowCountCheckConfig,
    run_id: str,
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    source_connector_type: Optional[str] = None,
    target_connector_type: Optional[str] = None,
) -> tuple[CheckResult, None]:
    """Compare row counts between source and target."""
    source_count = len(source_df)
    target_count = len(target_df)

    if source_count == 0 and target_count == 0:
        delta_pct = 0.0
    elif source_count == 0:
        delta_pct = 100.0
    else:
        delta_pct = abs(source_count - target_count) / source_count * 100.0

    status = "PASS" if delta_pct <= config.threshold_pct else "FAIL"

    result = CheckResult(
        run_id=run_id,
        check_name=config.name,
        check_type="row_count",
        status=status,
        actual_value=source_count,
        expected_value=target_count,
        delta=round(delta_pct, 6),
        source_connector_type=source_connector_type,
        target_connector_type=target_connector_type,
        reason=None if status == "PASS" else (
            f"delta {delta_pct:.2f}% exceeds threshold {config.threshold_pct}%"
        ),
    )
    return result, None  # Row Count never produces sample rows
