"""Translate one explicit at() context without evaluating Python context managers."""

import ast
import inspect

from sciloom.core.ir import DeviceAt
from sciloom.flow.device_slots import DeviceReference
from sciloom.flow.locations import at
from .context import LoweringContext
from .expressions import expression


def location_scope(context: LoweringContext, node: ast.With) -> DeviceAt:
    """Capture one declared logical slot and runtime Zone; the caller lowers body."""
    if len(node.items) != 1 or node.items[0].optional_vars is not None:
        context.fail("device_location_scope", "Use one with at(device, location) without an as target.", node)
    invocation = node.items[0].context_expr
    if not isinstance(invocation, ast.Call) or context.static_object(invocation.func) is not at:
        context.fail("device_location_scope", "Only with at(device, location) is supported at runtime.", node)
    names = [keyword.arg for keyword in invocation.keywords]
    if len(names) != len(set(names)) or None in names or any(isinstance(a, ast.Starred) for a in invocation.args):
        context.fail("call_binding", "at() does not accept duplicate or expanded arguments.", invocation)
    try:
        arguments = (
            inspect.signature(at)
            .bind(
                *invocation.args,
                **{k.arg: k.value for k in invocation.keywords if k.arg is not None},
            )
            .arguments
        )
    except TypeError as error:
        context.fail("call_binding", str(error), invocation)
    device = arguments["device"]
    if not isinstance(device, ast.Attribute) or not isinstance(device.value, ast.Name) or device.value.id != "self":
        context.fail("device_reference", "at() requires a declared self.<device> slot.", device)
    reference = context.host_attribute(device.attr)
    if not isinstance(reference, DeviceReference):
        context.fail(
            "device_reference", "at() requires a logical device reference, not hardware or a runtime variable.", device
        )
    return DeviceAt(
        **context.metadata(node),
        resource_id=context.device_resource(reference).node_id,
        location=expression(context, arguments["location"]),
    )
