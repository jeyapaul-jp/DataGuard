from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

import pandas as pd

from dataguard.execution.result import CheckResult


@runtime_checkable
class ResultsWriter(Protocol):
    def write(self, result: CheckResult, sample_df: Optional[pd.DataFrame]) -> None: ...
    def close(self) -> None: ...
