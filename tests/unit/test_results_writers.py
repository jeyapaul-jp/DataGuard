"""Tests for ResultsWriter protocol and FileWriter — tasks 6.1–6.2."""
import json
import pandas as pd
import pytest

from dataguard.results.protocol import ResultsWriter
from dataguard.results.file_writer import FileWriter
from dataguard.execution.result import CheckResult
from dataguard.config.models import FileOutputConfig


def _result(name="c1", status="PASS"):
    return CheckResult(run_id="run1", check_name=name, check_type="row_count", status=status)


# --- Protocol check (task 6.1) ---

class _BadWriter:
    def close(self): pass


class _GoodWriter:
    def write(self, result, sample_df): pass
    def close(self): pass


def test_class_missing_write_not_a_writer():
    assert not isinstance(_BadWriter(), ResultsWriter)


def test_class_with_both_methods_is_a_writer():
    assert isinstance(_GoodWriter(), ResultsWriter)


# --- FileWriter CSV append/overwrite (task 6.2) ---

def _file_cfg(tmp_path, overwrite=False, output_fields=None):
    return FileOutputConfig(
        type="csv",
        path=str(tmp_path / "results.csv"),
        overwrite=overwrite,
        output_fields=output_fields,
    )


def test_csv_file_created_on_first_write(tmp_path):
    writer = FileWriter(_file_cfg(tmp_path))
    writer.write(_result(), None)
    assert (tmp_path / "results.csv").exists()


def test_csv_appends_across_runs(tmp_path):
    cfg = _file_cfg(tmp_path)
    writer1 = FileWriter(cfg)
    writer1.write(_result("c1"), None)
    writer1.close()

    writer2 = FileWriter(cfg)
    writer2.write(_result("c2"), None)
    writer2.close()

    df = pd.read_csv(tmp_path / "results.csv")
    assert len(df) == 2


def test_csv_overwrite_replaces_file(tmp_path):
    cfg_append = _file_cfg(tmp_path)
    FileWriter(cfg_append).write(_result("c1"), None)

    cfg_overwrite = _file_cfg(tmp_path, overwrite=True)
    FileWriter(cfg_overwrite).write(_result("c2"), None)

    df = pd.read_csv(tmp_path / "results.csv")
    assert len(df) == 1
    assert df.iloc[0]["check_name"] == "c2"


def test_csv_output_fields_projection(tmp_path):
    cfg = _file_cfg(tmp_path, output_fields=["run_id", "check_name", "status"])
    FileWriter(cfg).write(_result(), None)
    df = pd.read_csv(tmp_path / "results.csv")
    assert list(df.columns) == ["run_id", "check_name", "status"]


def test_sample_rows_written_to_sidecar(tmp_path):
    cfg = _file_cfg(tmp_path)
    writer = FileWriter(cfg)
    r = _result("null_chk", "FAIL")
    sample = pd.DataFrame({"col": [None, None]})
    writer.write(r, sample)
    sidecar = tmp_path / "results_samples.csv"
    assert sidecar.exists()
    sdf = pd.read_csv(sidecar)
    assert "run_id" in sdf.columns
    assert "check_name" in sdf.columns


def test_unwritable_path_raises_on_init(tmp_path):
    import sys
    if sys.platform == "win32":
        pytest.skip("Windows file permission checks are different")
    import os
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    os.chmod(str(locked_dir), 0o444)
    with pytest.raises(OSError):
        FileWriter(FileOutputConfig(type="csv", path=str(locked_dir / "out.csv")))
    os.chmod(str(locked_dir), 0o755)
