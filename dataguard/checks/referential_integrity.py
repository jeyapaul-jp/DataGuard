from __future__ import annotations

from typing import Optional
import pandas as pd

from dataguard.config.models import ReferentialIntegrityCheckConfig
from dataguard.execution.result import CheckResult


def run_referential_integrity(
    config: ReferentialIntegrityCheckConfig,
    run_id: str,
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    source_connector_type: Optional[str] = None,
    target_connector_type: Optional[str] = None,
) -> tuple[CheckResult, Optional[pd.DataFrame]]:
    """Verify every non-NULL source value exists in the target reference column."""
    src_col = source_df[config.source_column]
    null_mask = src_col.isna()
    null_count = int(null_mask.sum())

    # Only check non-null source values
    non_null_source = source_df[~null_mask]
    target_values = set(target_df[config.target_column].dropna().unique())

    orphan_mask = ~non_null_source[config.source_column].isin(target_values)
    orphaned = non_null_source[orphan_mask]
    orphan_count = len(orphaned)

    status = "PASS" if orphan_count == 0 else "FAIL"
    sample = orphaned.head(config.sample_rows).copy() if status == "FAIL" else None

    result = CheckResult(
        run_id=run_id,
        check_name=config.name,
        check_type="referential_integrity",
        status=status,
        actual_value=orphan_count,
        expected_value=0,
        null_count=null_count,
        source_connector_type=source_connector_type,
        target_connector_type=target_connector_type,
        reason=None if status == "PASS" else (
            f"{orphan_count} orphaned values found "
            f"({null_count} NULLs excluded from check)"
        ),
    )
    return result, sample
