"""Lower property writes and registered lifecycle calls without invoking devices."""

import ast
import inspect

from ..core.ir import CommandArgument, ConfigureProperty, DeviceCommand, StartAgitation, StopAgitation
from ..core.ir.device_contracts import START_AGITATION_ID, STOP_AGITATION_ID
from ..devices.declarations import device_contract
from .context import LoweringContext
from .device_schema import DeviceReference
from .expressions import expression


def device_member(context: LoweringContext, node: ast.AST) -> tuple[DeviceReference, str] | None:
    if not (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name) and node.value.value.id == "self"):
        return None
    component = context.host_attribute(node.value.attr)
    return (component, node.attr) if isinstance(component, DeviceReference) else None


def configure(context: LoweringContext, node: ast.Assign) -> ConfigureProperty | None:
    member = device_member(context, node.targets[0])
    if member is None:
        return None
    reference, name = member
    contract = device_contract(context.device_type(reference))
    prop = next((p for p in contract.properties if p.name == name), None)
    if prop is None:
        context.fail("device_property", f"Device property {name!r} is not declared.", node.targets[0])
    return ConfigureProperty(
        **context.metadata(node),
        resource_id=context.device_resource(reference).node_id,
        property_id=prop.semantic_id,
        value=expression(context, node.value, prop.type),
    )


def operation(context: LoweringContext, node: ast.Call) -> StartAgitation | StopAgitation | DeviceCommand | None:
    member = device_member(context, node.func)
    if member is None:
        return None
    reference, name = member
    contract = device_contract(context.device_type(reference))
    command = next((c for c in contract.operations if c.name == name), None)
    if command is None:
        context.fail("unsupported_operation", f"Device command {name!r} is not declared.", node)
    if any(isinstance(arg, ast.Starred) for arg in node.args) or any(k.arg is None for k in node.keywords):
        context.fail("operation_binding", "Device calls do not support argument unpacking.", node)
    keywords: dict[str, ast.expr] = {}
    for keyword in node.keywords:
        assert keyword.arg is not None
        if keyword.arg in keywords:
            context.fail("operation_binding", "Duplicate device command argument.", node)
        keywords[keyword.arg] = keyword.value
    method = inspect.getattr_static(context.device_type(reference), name)
    try:
        arguments = inspect.signature(method).bind(None, *node.args, **keywords).arguments
    except TypeError as error:
        context.fail("operation_binding", str(error), node)
    resource_id = context.device_resource(reference).node_id
    if command.semantic_id in (START_AGITATION_ID, STOP_AGITATION_ID):
        cls = StartAgitation if command.semantic_id == START_AGITATION_ID else StopAgitation
        return cls(**context.metadata(node), resource_id=resource_id)
    return DeviceCommand(
        **context.metadata(node), resource_id=resource_id, operation_id=command.semantic_id,
        arguments=tuple(CommandArgument(name=p.name, value=expression(context, arguments[p.name], p.type))
                        for p in command.parameters),
    )
