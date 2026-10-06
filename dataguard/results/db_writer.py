from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from dataguard.config.models import DatabaseOutputConfig
from dataguard.execution.result import CheckResult


class DatabaseWriter:
    """Writes CheckResults and sample rows to a SQL database table."""

    def __init__(self, config: DatabaseOutputConfig, connections: dict) -> None:
        self._config = config
        self._fields = config.output_fields
        conn_cfg = connections.get(config.connection)
        if conn_cfg is None:
            raise ValueError(f"Output connection '{config.connection}' not found in connections")
        self._engine = create_engine(getattr(conn_cfg, "url", ""))
        self._table = config.table
        self._sample_table = config.table + "_samples"
        self._table_checked = False
        self._sample_table_checked = False

    def _project(self, row: dict) -> dict:
        if self._fields:
            return {k: row.get(k) for k in self._fields}
        return row

    def _ensure_table(self, table_name: str, sample_row: dict) -> None:
        inspector = inspect(self._engine)
        if not inspector.has_table(table_name):
            cols = ", ".join(f'"{k}" TEXT' for k in sample_row.keys())
            with self._engine.begin() as conn:
                conn.execute(text(f'CREATE TABLE "{table_name}" ({cols})'))
        else:
            existing_cols = {
                col["name"] for col in inspector.get_columns(table_name)
            }
            new_cols = set(sample_row.keys())
            extra = new_cols - existing_cols
            if extra:
                raise ValueError(
                    f"Results Store table '{table_name}' has a conflicting schema. "
                    f"Columns missing from table: {sorted(extra)}. "
                    f"Drop the table or reconfigure output_fields to match."
                )

    def write(self, result: CheckResult, sample_df: Optional[pd.DataFrame]) -> None:
        row = self._project(result.to_dict())

        if not self._table_checked:
            self._ensure_table(self._table, row)
            self._table_checked = True

        df = pd.DataFrame([row])
        df.to_sql(self._table, self._engine, if_exists="append", index=False)

        if sample_df is not None and not sample_df.empty:
            sdf = sample_df.copy()
            sdf.insert(0, "run_id", result.run_id)
            sdf.insert(1, "check_name", result.check_name)
            if not self._sample_table_checked:
                sample_row = {c: None for c in sdf.columns}
                self._ensure_table(self._sample_table, sample_row)
                self._sample_table_checked = True
            sdf.to_sql(self._sample_table, self._engine, if_exists="append", index=False)

    def close(self) -> None:
        self._engine.dispose()
