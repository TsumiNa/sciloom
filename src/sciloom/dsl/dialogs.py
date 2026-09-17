"""Lower whole-assignment dialog results without invoking author Python."""

import ast
import inspect

from sciloom.core.ir import AskYesNo, RequestText, ScalarType
from sciloom.flow.messages import ask_yes_no, request_text
from .context import LoweringContext
from .expressions import expression


def dialog_statement(context: LoweringContext, node: ast.stmt) -> RequestText | AskYesNo | None:
    """Recognize one result-producing marker with a declared destination."""
    if not isinstance(node, (ast.Expr, ast.Assign)) or not isinstance(node.value, ast.Call):
        return None
    invocation = node.value
    marker = context.static_object(invocation.func)
    if marker is not request_text and marker is not ask_yes_no:
        return None
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        context.fail("dialog_binding", "Assign dialog results as a complete RHS to one declared runtime field.", node)
    target = context.target(node.targets[0])
    names = [keyword.arg for keyword in invocation.keywords]
    if len(names) != len(set(names)) or None in names or any(isinstance(arg, ast.Starred) for arg in invocation.args):
        context.fail("call_binding", "Dialogs do not accept duplicate or expanded arguments.", invocation)
    try:
        bound = inspect.signature(marker).bind(
            *invocation.args,
            **{keyword.arg: keyword.value for keyword in invocation.keywords if keyword.arg is not None},
        )
    except TypeError as error:
        context.fail("call_binding", str(error), invocation)
    message = expression(context, bound.arguments["message"], ScalarType.TEXT)
    timeout_node = bound.arguments.get("timeout")
    absent = timeout_node is None or isinstance(timeout_node, ast.Constant) and timeout_node.value is None
    if isinstance(timeout_node, ast.Name) and timeout_node.id in context.source.static_names:
        absent = context.source.static_names[timeout_node.id] is None
    elif (
        isinstance(timeout_node, ast.Attribute)
        and isinstance(timeout_node.value, ast.Name)
        and timeout_node.value.id == "self"
        and timeout_node.attr not in context.instance.model_fields
    ):
        absent = context.host_attribute(timeout_node.attr) is None
    timeout = None
    if not absent:
        assert isinstance(timeout_node, ast.AST)
        timeout = expression(context, timeout_node, ScalarType.DURATION)
    kind = RequestText if marker is request_text else AskYesNo
    return kind(**context.metadata(invocation), target=target, message=message, timeout=timeout)
