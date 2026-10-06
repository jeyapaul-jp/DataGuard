from __future__ import annotations

import pandas as pd

from dataguard.config.models import DatabricksConnection
from .base import BaseConnector, ConnectorError


class DatabricksConnector(BaseConnector):
    """Connects to a Databricks SQL Warehouse via databricks-sql-connector (no JVM)."""

    def __init__(self, config: DatabricksConnection) -> None:
        self._config = config
        self._conn = None

    def connect(self) -> None:
        try:
            from databricks import sql as databricks_sql  # optional dependency
        except ImportError:
            raise ConnectorError(
                "Databricks connector requires 'databricks-sql-connector'. "
                "Install with: pip install 'dataguard[databricks]'"
            )
        try:
            self._conn = databricks_sql.connect(
                server_hostname=self._config.host,
                http_path=self._config.http_path,
                access_token=self._config.access_token,
            )
        except Exception as exc:
            raise ConnectorError(f"Databricks connection failed: {exc}") from exc

    def read(self, query_or_path: str, params: dict | None = None) -> pd.DataFrame:
        if self._conn is None:
            raise ConnectorError("DatabricksConnector.connect() must be called before read()")
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(query_or_path)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return pd.DataFrame(rows, columns=columns)
        except Exception as exc:
            raise ConnectorError(f"Databricks read failed: {exc}") from exc

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    @property
    def connector_type(self) -> str:
        return "databricks"
