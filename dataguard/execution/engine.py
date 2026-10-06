from __future__ import annotations

import sys
from typing import Optional

import pandas as pd

from dataguard.config.models import (
    DataguardConfig,
    RowCountCheckConfig, DuplicateCheckConfig, NullThresholdCheckConfig,
    ReferentialIntegrityCheckConfig, ReconciliationCheckConfig,
    CheckEndpoint,
)
from dataguard.connectors import make_connector, ConnectorError
from dataguard.checks import (
    run_row_count, run_duplicate_detection, run_null_threshold,
    run_referential_integrity, run_reconciliation,
)
from .result import CheckResult


def _get_connector_type(name: str, config: DataguardConfig) -> str:
    conn = config.connections.get(name)
    return getattr(conn, "type", "unknown") if conn else "unknown"


def _read_endpoint(
    endpoint: CheckEndpoint,
    config: DataguardConfig,
    missing_env_vars: dict[str, list[str]],
) -> tuple[pd.DataFrame, str]:
    """Connect and read from an endpoint. Returns (df, connector_type).
    Raises ConnectorError on any failure.
    """
    conn_name = endpoint.connection
    if conn_name in missing_env_vars:
        missing = ", ".join(missing_env_vars[conn_name])
        raise ConnectorError(
            f"Connection '{conn_name}' has unresolved environment variables: {missing}"
        )
    conn_config = config.connections.get(conn_name)
    if conn_config is None:
        raise ConnectorError(f"Unknown connection '{conn_name}'")

    connector = make_connector(conn_config)
    connector.connect()
    try:
        df = connector.read(endpoint.query or "")
    finally:
        connector.close()
    return df, getattr(connector, "connector_type", "unknown")


def run_checks(
    config: DataguardConfig,
    missing_env_vars: dict[str, list[str]],
    skip_names: set[str],
    writer,
) -> list[CheckResult]:
    """Execute all checks and write results. Returns list of CheckResult."""
    run_id = CheckResult.new_run_id()
    results: list[CheckResult] = []

    for check in config.checks:
        # --- SKIP ---
        if not check.enabled or check.name in skip_names:
            reason = (
                "enabled: false in config" if not check.enabled
                else f"excluded via --skip flag"
            )
            result = CheckResult(
                run_id=run_id,
                check_name=check.name,
                check_type=check.check_type,
                status="SKIP",
                source_connector_type=_get_connector_type(
                    check.source.connection, config
                ) if hasattr(check, "source") else None,
                reason=reason,
            )
            writer.write(result, None)
            results.append(result)
            continue

        # --- Execute ---
        try:
            result, sample_df = _run_single_check(check, run_id, config, missing_env_vars)
        except ConnectorError as exc:
            result = CheckResult(
                run_id=run_id,
                check_name=check.name,
                check_type=check.check_type,
                status="ERROR",
                reason=str(exc),
            )
            sample_df = None

        writer.write(result, sample_df)
        results.append(result)

    return results


def _run_single_check(
    check,
    run_id: str,
    config: DataguardConfig,
    missing_env_vars: dict[str, list[str]],
) -> tuple[CheckResult, Optional[pd.DataFrame]]:
    if isinstance(check, RowCountCheckConfig):
        src_df, src_type = _read_endpoint(check.source, config, missing_env_vars)
        tgt_df, tgt_type = _read_endpoint(check.target, config, missing_env_vars)
        return run_row_count(check, run_id, src_df, tgt_df, src_type, tgt_type)

    if isinstance(check, DuplicateCheckConfig):
        src_df, src_type = _read_endpoint(check.source, config, missing_env_vars)
        return run_duplicate_detection(check, run_id, src_df, src_type)

    if isinstance(check, NullThresholdCheckConfig):
        src_df, src_type = _read_endpoint(check.source, config, missing_env_vars)
        return run_null_threshold(check, run_id, src_df, src_type)

    if isinstance(check, ReferentialIntegrityCheckConfig):
        src_df, src_type = _read_endpoint(check.source, config, missing_env_vars)
        tgt_df, tgt_type = _read_endpoint(check.target, config, missing_env_vars)
        return run_referential_integrity(check, run_id, src_df, tgt_df, src_type, tgt_type)

    if isinstance(check, ReconciliationCheckConfig):
        src_df, src_type = _read_endpoint(check.source, config, missing_env_vars)
        tgt_df, tgt_type = _read_endpoint(check.target, config, missing_env_vars)
        return run_reconciliation(check, run_id, src_df, tgt_df, src_type, tgt_type)

    raise ValueError(f"Unhandled check type: {type(check).__name__}")
