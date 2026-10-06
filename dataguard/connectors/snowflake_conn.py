from __future__ import annotations

from pathlib import Path

import pandas as pd

from dataguard.config.models import SnowflakeConnection
from .base import BaseConnector, ConnectorError


class SnowflakeConnector(BaseConnector):
    """Connects to Snowflake using snowflake-connector-python (no JVM required)."""

    def __init__(self, config: SnowflakeConnection) -> None:
        self._config = config
        self._conn = None

    def connect(self) -> None:
        try:
            import snowflake.connector  # optional dependency
        except ImportError:
            raise ConnectorError(
                "Snowflake connector requires 'snowflake-connector-python'. "
                "Install with: pip install 'dataguard[snowflake]'"
            )
        try:
            params: dict = {
                "account": self._config.account,
                "warehouse": self._config.warehouse,
                "database": self._config.database,
                "schema": self._config.schema_name,
                "user": self._config.user,
            }
            if self._config.private_key_path:
                from cryptography.hazmat.primitives.serialization import (
                    load_pem_private_key, Encoding, PrivateFormat, NoEncryption
                )
                key_bytes = Path(self._config.private_key_path).read_bytes()
                private_key = load_pem_private_key(key_bytes, password=None)
                params["private_key"] = private_key.private_bytes(
                    Encoding.DER, PrivateFormat.PKCS8, NoEncryption()
                )
            else:
                params["password"] = self._config.password
            self._conn = snowflake.connector.connect(**params)
        except Exception as exc:
            raise ConnectorError(f"Snowflake connection failed: {exc}") from exc

    def read(self, query_or_path: str, params: dict | None = None) -> pd.DataFrame:
        if self._conn is None:
            raise ConnectorError("SnowflakeConnector.connect() must be called before read()")
        try:
            cursor = self._conn.cursor()
            cursor.execute(query_or_path)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        except Exception as exc:
            raise ConnectorError(f"Snowflake read failed: {exc}") from exc

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    @property
    def connector_type(self) -> str:
        return "snowflake"
