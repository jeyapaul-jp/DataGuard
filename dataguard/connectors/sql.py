from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from dataguard.config.models import SqlConnection
from .base import BaseConnector, ConnectorError


class SqlConnector(BaseConnector):
    """Connects to any SQLAlchemy-compatible database via DBAPI URL."""

    def __init__(self, config: SqlConnection) -> None:
        self._config = config
        self._engine = None

    def connect(self) -> None:
        try:
            self._engine = create_engine(self._config.url)
            # Probe the connection
            with self._engine.connect():
                pass
        except SQLAlchemyError as exc:
            raise ConnectorError(f"SQL connection failed ({self._config.url}): {exc}") from exc

    def read(self, query_or_path: str, params: dict | None = None) -> pd.DataFrame:
        if self._engine is None:
            raise ConnectorError("SqlConnector.connect() must be called before read()")
        try:
            with self._engine.connect() as conn:
                return pd.read_sql(text(query_or_path), conn)
        except SQLAlchemyError as exc:
            raise ConnectorError(f"SQL read failed: {exc}") from exc

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    @property
    def connector_type(self) -> str:
        return "sql"
