"""Typed logical CSV reads with captured arguments and atomic result binding."""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Iterable
from io import StringIO
from typing import TYPE_CHECKING

from sciloom.core.ir.csv import DEFAULT_USED, EOF, INVALID_DATA, IO_ERROR, OK
from sciloom.core.ir.model import CsvColumn, CsvErrorPolicy, CsvReadMode, ReadCsv
from sciloom.core.ir.types import QUANTITIES, ScalarType
from .environment import CsvReadEvent, _require_service
from .expressions import evaluate
from .values import RuntimeValue, ScalarValue, coerce, fail

if TYPE_CHECKING:
    from .runtime import Interpreter


def _cell(text: str, column: CsvColumn) -> ScalarValue:
    """Convert data, never expressions; raise ValueError for a bad cell."""
    if column.type == ScalarType.TEXT:
        return text
    value = text.strip(" \t\r\n")
    if column.type == ScalarType.BOOLEAN:
        if value.lower() not in ("true", "false"):
            raise ValueError("Expected true or false.")
        return value.lower() == "true"
    if column.type == ScalarType.INTEGER:
        if re.fullmatch(r"[+-]?[0-9]+", value) is None:
            raise ValueError("Expected an ASCII decimal integer.")
        return int(value)
    if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value) is None:
        raise ValueError("Expected a decimal number.")
    number = float(value)
    if column.type in QUANTITIES:
        assert column.unit is not None and isinstance(column.unit.value, (int, float))
        number *= column.unit.value
    if not math.isfinite(number) or (column.type == ScalarType.ROTATIONAL_SPEED and number < 0):
        raise ValueError("Value is not valid for the column quantity.")
    return number


def execute_read(session: Interpreter, node: ReadCsv, frame: dict[str, RuntimeValue]) -> None:
    """Evaluate one read once and commit only a completely checked result tuple."""
    path = evaluate(session, node.path, frame)
    assert isinstance(path, str)
    if not path or "\x00" in path:
        fail("csv_path", "CSV paths must be nonempty and contain no NUL.", node)
    row: int | None = None
    if node.row is not None:
        selected = evaluate(session, node.row, frame)
        if type(selected) is not int or selected < 0:
            fail("csv_index", "CSV selectors require nonnegative integers, excluding bool.", node.row)
        row = selected
    indices: list[int] = []
    defaults: list[ScalarValue | None] = []
    for column in node.columns:
        index = evaluate(session, column.index, frame)
        if type(index) is not int or index < 0:
            fail("csv_index", "CSV selectors require nonnegative integers, excluding bool.", column.index)
        indices.append(index)
        defaults.append(
            coerce(evaluate(session, column.default, frame), column.type, column.default)
            if column.default is not None
            else None
        )
    files = _require_service(session.environment.files, "files", node)
    status = OK
    columns: list[list[ScalarValue]] = [[] for _ in node.columns]
    try:
        data = files.read_bytes(path)
    except OSError:
        status = IO_ERROR
    except (ValueError, TypeError) as error:
        fail("csv_path", str(error), node)
    except Exception as error:
        fail("file_service_error", f"File service failed: {error}", node)
    else:
        if type(data) is not bytes:
            fail("file_service_error", "FileService.read_bytes must return immutable bytes.", node)
        try:
            reader = csv.reader(StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
            if node.header:
                next(reader, None)
            records: Iterable[list[str]]
            if node.mode == CsvReadMode.ROW:
                assert row is not None
                for _ in range(row):
                    if next(reader, None) is None:
                        break
                record = next(reader, None)
                records = () if record is None else (record,)
                if record is None:
                    status = EOF
            else:
                records = reader
            for record in records:
                for i, column in enumerate(node.columns):
                    try:
                        value = _cell(record[indices[i]], column)
                    except (IndexError, ValueError, OverflowError):
                        default = defaults[i]
                        if default is None:
                            status = INVALID_DATA
                            break
                        value = default
                        status = DEFAULT_USED
                    columns[i].append(value)
                if status == INVALID_DATA:
                    break
        except (UnicodeDecodeError, csv.Error):
            status = INVALID_DATA
    session._record_event(
        CsvReadEvent(
            node_id=node.node_id,
            source=node.source,
            path=path,
            mode=node.mode,
            header=node.header,
            row=row,
            columns=tuple(indices),
            status=status,
        )
    )
    if status in (EOF, INVALID_DATA, IO_ERROR) and node.error_policy == CsvErrorPolicy.RAISE:
        code = {EOF: "csv_eof", INVALID_DATA: "csv_invalid_data", IO_ERROR: "csv_io_error"}[status]
        fail(code, f"CSV read failed with status {status} for {path!r}; no result fields were changed.", node)
    values: tuple[RuntimeValue, ...]
    if status in (EOF, INVALID_DATA, IO_ERROR):
        if node.mode == CsvReadMode.ROW:
            assert all(value is not None for value in defaults)
            values = tuple(value for value in defaults if value is not None)
        else:
            values = tuple(() for _ in columns)
    elif node.mode == CsvReadMode.ROW:
        values = tuple(column[0] for column in columns)
    else:
        values = tuple(tuple(column) for column in columns)
    if node.error_policy == CsvErrorPolicy.STATUS:
        values = (status, *values)
    # Widening to a destination can itself fail (e.g. a huge integer to float).
    # Normalize every destination before writing any of them.
    committed = tuple(
        coerce(value, session._variables[target.symbol_id].type, target)
        for target, value in zip(node.targets, values, strict=True)
    )
    for target, result in zip(node.targets, committed, strict=True):
        session._write(target, result, frame)
