"""Recognize typed CSV metadata and fixed result bindings without host evaluation."""

import ast
import inspect

from sciloom.core.ir import CsvColumn, CsvErrorPolicy, CsvReadMode, ReadCsv, ScalarType
from sciloom.flow import csv
from sciloom.flow.fields import _value_type
from sciloom.units import DurationUnit, FlowRateUnit, LengthUnit, SpeedUnit, VolumeUnit
from .context import LoweringContext
from .expressions import expression, literal


def _metadata_value(context: LoweringContext, node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        if node.attr in context.instance.model_fields:
            context.fail("csv_metadata", "CSV header, type and unit metadata must be host-time values.", node)
        return context.host_attribute(node.attr)
    return context.static_object(node)


def csv_read(context: LoweringContext, assignment: ast.Assign) -> ReadCsv | None:
    """Lower an entire tuple-assignment read; leave other statements untouched."""
    invocation = assignment.value
    if not isinstance(invocation, ast.Call):
        return None
    marker = context.static_object(invocation.func)
    selected = next(
        (
            (function, mode, policy)
            for function, mode, policy in (
                (csv.read_row, CsvReadMode.ROW, CsvErrorPolicy.RAISE),
                (csv.read_columns, CsvReadMode.COLUMNS, CsvErrorPolicy.RAISE),
                (csv.try_read_row, CsvReadMode.ROW, CsvErrorPolicy.STATUS),
                (csv.try_read_columns, CsvReadMode.COLUMNS, CsvErrorPolicy.STATUS),
            )
            if marker is function
        ),
        None,
    )
    if selected is None:
        return None
    function, mode, policy = selected
    if not isinstance(assignment.targets[0], ast.Tuple):
        context.fail("csv_binding", "CSV reads require tuple unpacking, including a single result.", assignment)
    names = [keyword.arg for keyword in invocation.keywords]
    if len(names) != len(set(names)) or None in names or any(isinstance(arg, ast.Starred) for arg in invocation.args):
        context.fail("call_binding", "CSV reads do not accept duplicate or expanded arguments.", invocation)
    try:
        bound = inspect.signature(function).bind(
            *invocation.args,
            **{keyword.arg: keyword.value for keyword in invocation.keywords if keyword.arg is not None},
        )
    except TypeError as error:
        context.fail("call_binding", str(error), invocation)
    arguments = bound.arguments
    header = _metadata_value(context, arguments["header"])
    if type(header) is not bool:
        context.fail("csv_metadata", "CSV header must be a host Boolean.", arguments["header"])
    columns_node = arguments["columns"]
    if not isinstance(columns_node, ast.Tuple) or not columns_node.elts:
        context.fail("csv_columns", "CSV columns must be a nonempty tuple of inline Column declarations.", invocation)
    metadata = context.metadata(invocation)
    path = expression(context, arguments["path"])
    row = expression(context, arguments["row"]) if mode == CsvReadMode.ROW else None
    columns = []
    for column_node in columns_node.elts:
        if not isinstance(column_node, ast.Call) or context.static_object(column_node.func) is not csv.Column:
            context.fail("csv_columns", "Use inline csv.Column declarations.", column_node)
        names = [keyword.arg for keyword in column_node.keywords]
        if (
            column_node.args
            or len(names) != len(set(names))
            or None in names
            or not {"index", "value_type"} <= set(names)
            or set(names) - {"index", "value_type", "unit", "default"}
        ):
            context.fail(
                "csv_columns", "Column requires index/value_type and optional unit/default keywords.", column_node
            )
        keywords = {keyword.arg: keyword.value for keyword in column_node.keywords}
        try:
            scalar = _value_type("csv.Column", _metadata_value(context, keywords["value_type"]))
        except (TypeError, ValueError) as error:
            context.fail("csv_columns", str(error), keywords["value_type"])
        if not isinstance(scalar, ScalarType):
            context.fail("csv_columns", "Each CSV column declares a scalar element type.", column_node)
        index = expression(context, keywords["index"])
        unit = None
        if "unit" in keywords:
            unit_value = _metadata_value(context, keywords["unit"])
            if unit_value is not None:
                if not isinstance(unit_value, (SpeedUnit, VolumeUnit, DurationUnit, FlowRateUnit, LengthUnit)):
                    context.fail("csv_unit", "CSV unit must be a host SciLoom physical unit.", keywords["unit"])
                unit = literal(context, keywords["unit"], 1 * unit_value)
        default = expression(context, keywords["default"], scalar) if "default" in keywords else None
        columns.append(CsvColumn(index=index, type=scalar, unit=unit, default=default))
    return ReadCsv(
        **metadata,
        mode=mode,
        error_policy=policy,
        path=path,
        header=header,
        row=row,
        columns=tuple(columns),
        targets=tuple(context.target(target) for target in assignment.targets[0].elts),
    )
