"""Lower a CSV row append without evaluating author code or touching files."""

import ast
import inspect

from sciloom.core.ir import AppendCsv, CsvErrorPolicy
from sciloom.flow import csv
from .context import LoweringContext
from .expressions import expression


def csv_append(context: LoweringContext, node: ast.stmt) -> AppendCsv | None:
    """Recognize a standalone append or a complete status assignment."""
    if not isinstance(node, (ast.Expr, ast.Assign)) or not isinstance(node.value, ast.Call):
        return None
    invocation = node.value
    marker = context.static_object(invocation.func)
    if marker is not csv.append_row and marker is not csv.try_append_row:
        return None
    target = None
    if marker is csv.try_append_row:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            context.fail("csv_binding", "Assign try_append_row(...) to one declared integer field.", node)
        target = context.target(node.targets[0])
    elif not isinstance(node, ast.Expr):
        context.fail("csv_binding", "append_row(...) is a standalone statement with no result.", node)
    names = [keyword.arg for keyword in invocation.keywords]
    if len(names) != len(set(names)) or None in names or any(isinstance(arg, ast.Starred) for arg in invocation.args):
        context.fail("call_binding", "CSV appends do not accept duplicate or expanded arguments.", invocation)
    try:
        bound = inspect.signature(marker).bind(
            *invocation.args,
            **{keyword.arg: keyword.value for keyword in invocation.keywords if keyword.arg is not None},
        )
    except TypeError as error:
        context.fail("call_binding", str(error), invocation)
    values = bound.arguments["values"]
    if not isinstance(values, ast.Tuple) or not values.elts:
        context.fail("csv_values", "CSV values must be a nonempty inline tuple of scalar expressions.", values)
    return AppendCsv(
        **context.metadata(invocation),
        path=expression(context, bound.arguments["path"]),
        values=tuple(expression(context, value) for value in values.elts),
        error_policy=CsvErrorPolicy.STATUS if target is not None else CsvErrorPolicy.RAISE,
        status=target,
    )
