from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from dataguard.config.models import FileOutputConfig, RESULT_RECORD_FIELDS
from dataguard.execution.result import CheckResult


class FileWriter:
    """Writes CheckResults and sample rows to a CSV or JSON file."""

    def __init__(self, config: FileOutputConfig) -> None:
        self._config = config
        self._path = Path(config.path)
        self._sidecar = self._path.with_name(
            self._path.stem + "_samples" + self._path.suffix
        )
        self._fields = config.output_fields  # None = all fields
        self._first_write = True
        self._first_sample_write = True
        self._validate_writable()
        if config.overwrite:
            self._path.unlink(missing_ok=True)
            self._sidecar.unlink(missing_ok=True)

    def _validate_writable(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            test = self._path.parent / ".dataguard_write_test"
            test.touch()
            test.unlink()
        except OSError as exc:
            raise OSError(
                f"Results Store path '{self._path}' is not writable: {exc}"
            ) from exc

    def _project(self, row: dict) -> dict:
        if self._fields:
            return {k: row.get(k) for k in self._fields}
        return row

    def _write_rows(self, path: Path, rows: list[dict], first_ref: bool) -> bool:
        df = pd.DataFrame(rows)
        if self._config.type == "csv":
            write_header = first_ref or not path.exists()
            df.to_csv(path, mode="a", header=write_header, index=False)
        else:
            existing: list[dict] = []
            if path.exists() and not self._config.overwrite:
                try:
                    existing = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, ValueError):
                    existing = []
            existing.extend(rows)
            path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
        return False  # subsequent writes are not "first"

    def write(self, result: CheckResult, sample_df: Optional[pd.DataFrame]) -> None:
        row = self._project(result.to_dict())
        self._first_write = self._write_rows(self._path, [row], self._first_write)

        if sample_df is not None and not sample_df.empty:
            sample_rows = sample_df.copy()
            sample_rows.insert(0, "run_id", result.run_id)
            sample_rows.insert(1, "check_name", result.check_name)
            self._first_sample_write = self._write_rows(
                self._sidecar, sample_rows.to_dict(orient="records"), self._first_sample_write
            )

    def close(self) -> None:
        pass  # Files are flushed on each write
