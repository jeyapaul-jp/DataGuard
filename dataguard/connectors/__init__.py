from .base import BaseConnector, ConnectorError
from .sql import SqlConnector
from .file import CsvConnector, ParquetConnector, JsonConnector
from .snowflake_conn import SnowflakeConnector
from .databricks_conn import DatabricksConnector
from dataguard.config.models import (
    SqlConnection, SnowflakeConnection, DatabricksConnection,
    CsvConnection, ParquetConnection, JsonConnection,
)

__all__ = [
    "BaseConnector", "ConnectorError",
    "SqlConnector", "CsvConnector", "ParquetConnector", "JsonConnector",
    "SnowflakeConnector", "DatabricksConnector",
    "make_connector",
]


def make_connector(conn_config) -> "BaseConnector":
    if isinstance(conn_config, SqlConnection):
        return SqlConnector(conn_config)
    if isinstance(conn_config, SnowflakeConnection):
        return SnowflakeConnector(conn_config)
    if isinstance(conn_config, DatabricksConnection):
        return DatabricksConnector(conn_config)
    if isinstance(conn_config, CsvConnection):
        return CsvConnector(conn_config)
    if isinstance(conn_config, ParquetConnection):
        return ParquetConnector(conn_config)
    if isinstance(conn_config, JsonConnection):
        return JsonConnector(conn_config)
    raise ConnectorError(f"Unknown connection type: {type(conn_config).__name__}")
