from __future__ import annotations

from pathlib import Path

import pandas as pd

from dataguard.config.models import CsvConnection, ParquetConnection, JsonConnection
from .base import BaseConnector, ConnectorError

_CLOUD_PREFIXES = ("s3://", "abfs://", "az://", "gs://", "gcs://")

_CLOUD_EXTRAS = {
    "s3://": ("s3fs", "dataguard[s3]"),
    "abfs://": ("adlfs", "dataguard[azure]"),
    "az://": ("adlfs", "dataguard[azure]"),
    "gs://": ("gcsfs", "dataguard[gcs]"),
    "gcs://": ("gcsfs", "dataguard[gcs]"),
}


def _is_cloud(path: str) -> bool:
    return any(path.startswith(p) for p in _CLOUD_PREFIXES)


def _check_cloud_dep(path: str) -> None:
    for prefix, (module, extra) in _CLOUD_EXTRAS.items():
        if path.startswith(prefix):
            try:
                __import__(module)
            except ImportError:
                raise ConnectorError(
                    f"Cloud storage path '{path}' requires the '{module}' package. "
                    f"Install it with: pip install '{extra}'"
                )
            return


def _resolve_path(path: str) -> str:
    if _is_cloud(path):
        _check_cloud_dep(path)
        return path
    return str(Path(path))


class CsvConnector(BaseConnector):
    def __init__(self, config: CsvConnection) -> None:
        self._config = config

    def connect(self) -> None:
        path = _resolve_path(self._config.path)
        if not _is_cloud(path) and not Path(path).exists():
            raise ConnectorError(f"CSV file not found: {path}")

    def read(self, query_or_path: str = "", params: dict | None = None) -> pd.DataFrame:
        path = _resolve_path(self._config.path)
        try:
            return pd.read_csv(path)
        except FileNotFoundError as exc:
            raise ConnectorError(f"CSV file not found: {path}") from exc
        except Exception as exc:
            raise ConnectorError(f"Failed to read CSV '{path}': {exc}") from exc

    @property
    def connector_type(self) -> str:
        return "csv"


class ParquetConnector(BaseConnector):
    def __init__(self, config: ParquetConnection) -> None:
        self._config = config

    def connect(self) -> None:
        path = _resolve_path(self._config.path)
        if not _is_cloud(path) and not Path(path).exists():
            raise ConnectorError(f"Parquet file not found: {path}")

    def read(self, query_or_path: str = "", params: dict | None = None) -> pd.DataFrame:
        path = _resolve_path(self._config.path)
        try:
            return pd.read_parquet(path)
        except FileNotFoundError as exc:
            raise ConnectorError(f"Parquet file not found: {path}") from exc
        except Exception as exc:
            raise ConnectorError(f"Failed to read Parquet '{path}': {exc}") from exc

    @property
    def connector_type(self) -> str:
        return "parquet"


class JsonConnector(BaseConnector):
    def __init__(self, config: JsonConnection) -> None:
        self._config = config

    def connect(self) -> None:
        path = _resolve_path(self._config.path)
        if not _is_cloud(path) and not Path(path).exists():
            raise ConnectorError(f"JSON file not found: {path}")

    def read(self, query_or_path: str = "", params: dict | None = None) -> pd.DataFrame:
        path = _resolve_path(self._config.path)
        try:
            return pd.read_json(path)
        except FileNotFoundError as exc:
            raise ConnectorError(f"JSON file not found: {path}") from exc
        except Exception as exc:
            raise ConnectorError(f"Failed to read JSON '{path}': {exc}") from exc

    @property
    def connector_type(self) -> str:
        return "json"
