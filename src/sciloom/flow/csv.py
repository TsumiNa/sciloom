"""Typed runtime CSV reads and explicit row appends."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

from sciloom.core.ir.csv import (
    DEFAULT_USED as DEFAULT_USED,
    EOF as EOF,
    INVALID_DATA as INVALID_DATA,
    IO_ERROR as IO_ERROR,
    OK as OK,
)
from sciloom.core.ir.types import ListType
from sciloom.units import Duration, DurationUnit, RotationalSpeed, SpeedUnit, Volume, VolumeUnit
from .fields import _default, _value_type

T = TypeVar("T", int, float, bool, str, RotationalSpeed, Volume, Duration)


class _Omitted(Enum):
    DEFAULT = "omitted"


@dataclass(frozen=True, kw_only=True)
class Column(Generic[T]):
    """Describe one zero-based CSV column in a runtime read call.

    Args:
        index: Nonnegative runtime integer selector, excluding bool.
        value_type: Native scalar or physical quantity type of each result.
        unit: Required matching unit for quantities; omitted for ordinary scalars.
        default: Optional typed fallback for a missing or invalid cell. It never
            recovers a file error and is not multiplied by the column unit.

    Raises:
        TypeError: A selector or unit is of the wrong type.
        ValueError: A selector is negative or metadata/defaults are invalid.

    Inline Column calls inside runtime methods are analyzed without executing
    Python constructors. Their selectors and defaults are captured at run time.
    """

    index: int
    value_type: type[T]
    unit: SpeedUnit | VolumeUnit | DurationUnit | None = None
    default: T | _Omitted = _Omitted.DEFAULT

    def __post_init__(self) -> None:
        if type(self.index) is not int:
            raise TypeError("CSV column indices require integers, excluding bool.")
        if self.index < 0:
            raise ValueError("CSV column indices must be nonnegative.")
        value_type = _value_type("csv.Column", self.value_type)
        if isinstance(value_type, ListType):
            raise TypeError("CSV columns require scalar element types.")
        quantity = self.value_type in (RotationalSpeed, Volume, Duration)
        if self.unit is None:
            if quantity:
                raise ValueError("Physical CSV columns require an explicit matching unit.")
        elif not isinstance(self.unit, (SpeedUnit, VolumeUnit, DurationUnit)):
            raise TypeError("CSV units must be SciLoom physical units.")
        elif type(1 * self.unit) is not self.value_type:
            raise ValueError("CSV unit does not match the column type.")
        if self.default is not _Omitted.DEFAULT:
            _default("csv.Column", self.default, value_type)


def read_row(path: str, *, row: int, header: bool, columns: tuple[Column[Any], ...]) -> tuple[Any, ...]:
    """Read one zero-based data row into a tuple of typed scalar values.

    Args:
        path: Runtime CSV path supplied to the execution environment or target.
        row: Zero-based data row, after an optional header.
        header: Host Boolean selecting whether to skip the first record.
        columns: Nonempty tuple of inline Column descriptors.

    Returns:
        One scalar per column, including a tuple for a single column.

    Raises:
        TypeError: Called from host Python rather than written in a runtime method.
        sciloom.core.diagnostics.ExecutionError: The file, row or data is invalid;
            no destination is partially updated.
    """
    raise TypeError("CSV reads belong in compiled @runtime methods.")


def read_columns(path: str, *, header: bool, columns: tuple[Column[Any], ...]) -> tuple[Any, ...]:
    """Read selected columns into independent aligned typed lists.

    Args:
        path: Runtime file path.
        header: Host Boolean selecting whether to skip the first record.
        columns: Nonempty tuple of inline Column descriptors.

    Returns:
        One list per column. Empty datasets return empty lists.

    Raises:
        TypeError: Called by host Python.
        sciloom.core.diagnostics.ExecutionError: The read fails without committing
            any result fields; individual columns may provide cell defaults.
    """
    raise TypeError("CSV reads belong in compiled @runtime methods.")


def try_read_row(path: str, *, row: int, header: bool, columns: tuple[Column[Any], ...]) -> tuple[Any, ...]:
    """Return an integer status followed by every scalar column result.

    Args:
        path: Runtime file path.
        row: Zero-based data row after an optional header.
        header: Host Boolean header selection.
        columns: Nonempty inline descriptors, each with an explicit default.

    Returns:
        Flat tuple of status and values; whole-read failure returns all defaults.
        Status is OK, DEFAULT_USED, EOF, INVALID_DATA or IO_ERROR.

    Raises:
        TypeError: Called by host Python.
        sciloom.core.diagnostics.ExecutionError: Selectors/defaults are invalid
            or the reference file service is missing, rather than a CSV failure.
    """
    raise TypeError("CSV reads belong in compiled @runtime methods.")


def try_read_columns(path: str, *, header: bool, columns: tuple[Column[Any], ...]) -> tuple[Any, ...]:
    """Return an integer status followed by every column list.

    Args:
        path: Runtime file path.
        header: Host Boolean header selection.
        columns: Nonempty tuple of inline Column descriptors.

    Returns:
        Flat tuple of status and aligned lists; whole-read failure returns all
        empty lists. Empty data succeeds with OK and empty lists.

    Raises:
        TypeError: Called by host Python.
        sciloom.core.diagnostics.ExecutionError: Invalid arguments or a missing
            reference file service; these are not recoverable CSV statuses.
    """
    raise TypeError("CSV reads belong in compiled @runtime methods.")


def append_row(
    path: str, *, values: tuple[int | float | bool | str | RotationalSpeed | Volume | Duration, ...]
) -> None:
    """Append one ordered scalar row, stopping execution on a file error.

    Args:
        path: Runtime file path. Parent directories must already exist.
        values: Nonempty inline tuple of scalar or physical quantity expressions.

    Raises:
        TypeError: Called from host Python instead of a runtime method.
        sciloom.core.diagnostics.ExecutionError: The write or encoding fails, or
            the reference file service is missing.

    Arguments are captured once. Reference execution writes UTF-8, comma-separated
    cells and a CRLF record terminator; quantities use canonical SI numbers.
    Existing content must end at a complete record boundary. Earlier or partial
    writes are not rolled back. AutoSuite compilation awaits native mode and
    encoding verification.
    """
    raise TypeError("CSV appends belong in compiled @runtime methods.")


def try_append_row(
    path: str, *, values: tuple[int | float | bool | str | RotationalSpeed | Volume | Duration, ...]
) -> int:
    """Append one row and assign OK or IO_ERROR to one integer runtime field.

    Args:
        path: Runtime file path; no parent directories are created.
        values: Nonempty inline tuple captured before the single write attempt.

    Returns:
        OK after a successful write, or IO_ERROR after a file error. Partial
        writes are not rolled back and this operation never retries.

    Raises:
        TypeError: Called from host Python.
        sciloom.core.diagnostics.ExecutionError: Invalid arguments, encoding
            failure, a missing file service or a broken service implementation.

    Assign the entire call result to one declared integer field. Encoding and
    existing-file requirements are the same as append_row.
    """
    raise TypeError("CSV appends belong in compiled @runtime methods.")
