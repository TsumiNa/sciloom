"""Recognize clock vocabulary without executing timer objects or host calls."""

import ast

from sciloom.core.ir import StartTimer, Wait, WaitUntil
from sciloom.flow.timing import wait
from .context import LoweringContext
from .expressions import expression


def timing_statement(context: LoweringContext, node: ast.Call) -> StartTimer | Wait | WaitUntil | None:
    """Lower standalone wait and declared self.timer commands."""
    resource_id = None
    method = "wait"
    if context.static_object(node.func) is not wait:
        member = node.func
        if not (
            isinstance(member, ast.Attribute)
            and isinstance(member.value, ast.Attribute)
            and isinstance(member.value.value, ast.Name)
            and member.value.value.id == "self"
            and member.value.attr in context.instance.timer_fields
        ):
            return None
        resource_id = f"{context.function_id}:timer:{member.value.attr}"
        method = member.attr
        if method == "start":
            if node.args or node.keywords:
                context.fail("call_binding", "Timer.start takes no arguments.", node)
            return StartTimer(**context.metadata(node), resource_id=resource_id)
        if method != "wait_until":
            context.fail("timer_operation", "Timers only support start() and wait_until(duration).", node)
    if len(node.args) == 1 and not node.keywords and not isinstance(node.args[0], ast.Starred):
        duration_node = node.args[0]
    elif not node.args and len(node.keywords) == 1 and node.keywords[0].arg == "duration":
        duration_node = node.keywords[0].value
    else:
        context.fail("call_binding", f"{method} requires exactly one duration argument.", node)
    metadata = context.metadata(node)
    duration = expression(context, duration_node)
    if resource_id is None:
        return Wait(**metadata, duration=duration)
    return WaitUntil(**metadata, resource_id=resource_id, duration=duration)
