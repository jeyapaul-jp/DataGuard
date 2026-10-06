from __future__ import annotations

from typing import Optional
import pandas as pd

from dataguard.config.models import DuplicateCheckConfig
from dataguard.execution.result import CheckResult


def run_duplicate_detection(
    config: DuplicateCheckConfig,
    run_id: str,
    source_df: pd.DataFrame,
    source_connector_type: Optional[str] = None,
) -> tuple[CheckResult, Optional[pd.DataFrame]]:
    """Detect duplicate rows in source_df based on key_columns."""
    dupes = source_df[source_df.duplicated(subset=config.key_columns, keep=False)]
    dup_count = len(dupes)

    if dup_count == 0:
        status = "PASS"
        sample = None
    else:
        status = "FAIL"
        sample = dupes.head(config.sample_rows).copy()

    result = CheckResult(
        run_id=run_id,
        check_name=config.name,
        check_type="duplicate",
        status=status,
        actual_value=dup_count,
        expected_value=0,
        source_connector_type=source_connector_type,
        reason=None if status == "PASS" else f"{dup_count} duplicate rows found",
    )
    return result, sample
