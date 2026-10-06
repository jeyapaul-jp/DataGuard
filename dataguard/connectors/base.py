from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class ConnectorError(Exception):
    """Raised when a connector cannot connect or read data."""


class BaseConnector(ABC):
    """Abstract base for all DataGuard data-source connectors."""

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the data store."""

    @abstractmethod
    def read(self, query_or_path: str, params: dict | None = None) -> pd.DataFrame:
        """Execute a query or read a file and return a DataFrame."""

    def close(self) -> None:
        """Release any held resources. Override if needed."""
