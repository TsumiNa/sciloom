"""Host CSV declarations validate metadata; runtime reads never perform host IO."""

import subprocess
import sys

import pytest

from sciloom import Volume, csv, mL, s


def test_column_metadata_defaults_and_host_read_guards():
    assert csv.Column(index=0, value_type=float, default=1).default == 1
    assert csv.Column(index=1, value_type=Volume, unit=mL, default=2 * mL).default == 2 * mL
    for kwargs in (
        {"index": True, "value_type": str},
        {"index": -1, "value_type": str},
        {"index": 0, "value_type": list[str]},
        {"index": 0, "value_type": str, "default": 1},
        {"index": 0, "value_type": float, "unit": mL},
        {"index": 0, "value_type": Volume},
        {"index": 0, "value_type": Volume, "unit": s},
    ):
        with pytest.raises((TypeError, ValueError)):
            csv.Column(**kwargs)
    for marker in (csv.read_row, csv.try_read_row, csv.read_columns, csv.try_read_columns):
        kwargs = {"row": 0} if marker in (csv.read_row, csv.try_read_row) else {}
        with pytest.raises(TypeError, match="@runtime"):
            marker("never-read.csv", header=False, columns=(csv.Column(index=0, value_type=str, default=""),), **kwargs)


def test_mypy_checks_column_element_defaults_and_read_arguments(tmp_path):
    valid = tmp_path / "valid.py"
    valid.write_text("""from typing import assert_type
from sciloom import csv, Volume, mL
column = csv.Column(index=0, value_type=str, default="fallback")
assert_type(column, csv.Column[str])
csv.Column(index=1, value_type=Volume, unit=mL, default=1 * mL)
csv.read_columns("file.csv", header=True, columns=(column,))
""")
    invalid = tmp_path / "invalid.py"
    invalid.write_text("""from sciloom import csv
csv.Column(index=0, value_type=str, default=1)
csv.read_columns(3, header=True, columns=())
csv.read_row("file.csv", row="first", header=False, columns=())
""")
    for path, expected in ((valid, 0), (invalid, 1)):
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--cache-dir", str(tmp_path / "cache"), str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        if expected:
            assert result.stdout.count(" error: ") == 3, result.stdout
