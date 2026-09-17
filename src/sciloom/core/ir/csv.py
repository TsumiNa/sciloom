"""CSV result bindings and scalar/unit rules, shared by source and JSON programs."""

import math

from .expressions import ExpressionChecker
from .model import AppendCsv, CsvErrorPolicy, CsvReadMode, Expression, FunctionIR, Literal, ReadCsv
from .types import QUANTITIES, THERMAL_QUANTITIES, ListType, ScalarType, ValueType, is_assignable

OK = 0
DEFAULT_USED = 1
EOF = 2
INVALID_DATA = 3
IO_ERROR = 4


def validate_append(node: AppendCsv, function: FunctionIR, path: str, checker: ExpressionChecker) -> None:
    """Check path, scalar row and the single optional status binding."""
    report = checker.report
    if checker.check(node.path, function, f"{path}.path") not in (None, ScalarType.TEXT):
        report("csv_path", "CSV paths must be text.", f"{path}.path", node.path)
    if isinstance(node.path, Literal) and isinstance(node.path.value, str):
        if not node.path.value or "\x00" in node.path.value:
            report("csv_path", "CSV paths must be nonempty and contain no NUL.", f"{path}.path", node.path)
    if not node.values:
        report("csv_values", "CSV append requires at least one scalar value.", path, node)
    for i, value in enumerate(node.values):
        kind = checker.check(value, function, f"{path}.values[{i}]")
        if kind is not None and not isinstance(kind, ScalarType):
            report(
                "csv_values", "CSV append values must be scalars or physical quantities.", f"{path}.values[{i}]", value
            )
    if (node.status is not None) != (node.error_policy == CsvErrorPolicy.STATUS):
        report("csv_binding", "Only try-append requires one integer status destination.", path, node)
    if node.status is not None:
        if checker.check(node.status, function, f"{path}.status") not in (None, ScalarType.INTEGER):
            report("csv_binding", "CSV append status requires an integer destination.", f"{path}.status", node.status)


def validate_csv(node: ReadCsv, function: FunctionIR, path: str, checker: ExpressionChecker) -> None:
    """Check one typed read, reporting errors without changing the operation."""
    report = checker.report
    if checker.check(node.path, function, f"{path}.path") not in (None, ScalarType.TEXT):
        report("csv_path", "CSV paths must be text.", f"{path}.path", node.path)
    if isinstance(node.path, Literal) and isinstance(node.path.value, str):
        if not node.path.value or "\x00" in node.path.value:
            report("csv_path", "CSV paths must be nonempty and contain no NUL.", f"{path}.path", node.path)
    if (node.row is not None) != (node.mode == CsvReadMode.ROW):
        report("csv_row", "Only row reads require a row selector.", path, node)

    def index(value: Expression, location: str) -> None:
        if checker.check(value, function, location) not in (None, ScalarType.INTEGER):
            report("csv_index", "CSV selectors require nonnegative integers, excluding bool.", location, value)
        if isinstance(value, Literal) and type(value.value) is int and value.value < 0:
            report("csv_index", "CSV selectors must be nonnegative.", location, value)

    if node.row is not None:
        index(node.row, f"{path}.row")
    if not node.columns:
        report("csv_columns", "CSV reads require at least one typed column.", path, node)
    result_types: list[ValueType] = [ScalarType.INTEGER] if node.error_policy == CsvErrorPolicy.STATUS else []
    for i, column in enumerate(node.columns):
        location = f"{path}.columns[{i}]"
        if column.type in THERMAL_QUANTITIES:
            report("unsupported_csv_type", "Thermal CSV reads require an explicit conversion contract.", location, node)
        index(column.index, f"{location}.index")
        if column.unit is not None:
            checker.check(column.unit, function, f"{location}.unit")
            try:
                valid = (
                    column.type in QUANTITIES
                    and column.unit.type == column.type
                    and type(column.unit.value) in (int, float)
                    and isinstance(column.unit.value, (int, float))
                    and math.isfinite(column.unit.value)
                    and column.unit.value > 0
                )
            except OverflowError:
                valid = False
            if not valid:
                report(
                    "csv_unit",
                    "CSV units must be positive finite literals of the column quantity type.",
                    location,
                    node,
                )
        elif column.type in QUANTITIES:
            report("csv_unit", "Physical CSV columns require an explicit matching unit.", location, node)
        if column.default is not None:
            default_type = checker.check(column.default, function, f"{location}.default")
            if default_type is not None and not is_assignable(default_type, column.type):
                report("csv_default", "CSV default must match the column type.", location, column.default)
        elif node.mode == CsvReadMode.ROW and node.error_policy == CsvErrorPolicy.STATUS:
            report("csv_default", "try_read_row requires a default for every column.", location, node)
        result_types.append(ListType(element_type=column.type) if node.mode == CsvReadMode.COLUMNS else column.type)
    if len(node.targets) != len(result_types):
        report("csv_binding", "Bind every CSV result, including the status for status-form reads.", path, node)
    if len({target.symbol_id for target in node.targets}) != len(node.targets):
        report("csv_binding", "CSV result destinations must be distinct fields.", path, node)
    for i, target in enumerate(node.targets):
        target_type = checker.check(target, function, f"{path}.targets[{i}]")
        if target_type is not None and i < len(result_types):
            status_target = node.error_policy == CsvErrorPolicy.STATUS and i == 0
            if (status_target and target_type != ScalarType.INTEGER) or not is_assignable(result_types[i], target_type):
                report("csv_binding", "CSV destination type does not match its result.", f"{path}.targets[{i}]", target)
