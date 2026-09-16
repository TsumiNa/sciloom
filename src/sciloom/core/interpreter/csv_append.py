"""Capture and encode one logical CSV row before a single explicit file write."""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

from sciloom.core.ir.csv import IO_ERROR, OK
from sciloom.core.ir.model import AppendCsv, CsvErrorPolicy
from sciloom.core.ir.types import ScalarType
from sciloom.core.locations import Zone
from .environment import CsvAppendEvent, _require_service
from .expressions import evaluate
from .files import _InvalidFilePath
from .values import RuntimeValue, ScalarValue, fail, output_value

if TYPE_CHECKING:
    from .runtime import Interpreter


def execute_append(session: Interpreter, node: AppendCsv, frame: dict[str, RuntimeValue]) -> None:
    """Append once; file errors retain any partial external effects."""
    path = evaluate(session, node.path, frame)
    assert isinstance(path, str)
    if not path or "\x00" in path:
        fail("csv_path", "CSV paths must be nonempty and contain no NUL.", node.path)
    types: list[ScalarType] = []
    values: list[ScalarValue] = []
    for expression in node.values:
        value = evaluate(session, expression, frame)
        kind = session._expression_types[expression.node_id]
        assert isinstance(kind, ScalarType) and not isinstance(value, (tuple, Zone))
        types.append(kind)
        values.append(value)
    # Quantity values are already canonical SI scalars; only Boolean spelling
    # differs from the Python writer's standard scalar-to-text conversion.
    try:
        cells = [("true" if value else "false") if type(value) is bool else str(value) for value in values]
        buffer = StringIO(newline="")
        csv.writer(buffer, lineterminator="\r\n").writerow(cells)
        payload = buffer.getvalue().encode("utf-8")
    except (ValueError, csv.Error) as error:
        fail("csv_encoding", f"CSV row cannot be encoded as UTF-8: {error}", node)
    files = _require_service(session.environment.files, "files", node)
    status = OK
    try:
        # Check third-party implementations at runtime despite the None protocol.
        returned = files.append_bytes(path, payload)  # type: ignore[func-returns-value]
    except _InvalidFilePath as error:
        fail("csv_path", str(error), node)
    except OSError:
        status = IO_ERROR
    except Exception as error:
        fail("file_service_error", f"File service failed: {error}", node)
    else:
        if returned is not None:
            fail("file_service_error", "FileService.append_bytes must return None.", node)
    session._record_event(
        CsvAppendEvent(
            node_id=node.node_id,
            source=node.source,
            path=path,
            types=tuple(types),
            values=tuple(output_value(value, kind) for value, kind in zip(values, types, strict=True)),
            status=status,
        )
    )
    if status != OK and node.error_policy == CsvErrorPolicy.RAISE:
        fail("csv_io_error", f"CSV append failed for {path!r}; prior or partial bytes are not rolled back.", node)
    if node.status is not None:
        session._write(node.status, status, frame)
