"""Lower property writes and registered lifecycle calls without invoking devices."""

import ast

from ..core.ir import ConfigureProperty, StartAgitation, StopAgitation
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
    contract = device_contract(reference.device_type)
    prop = next((p for p in contract.properties if p.name == name), None)
    if prop is None:
        context.fail("device_property", f"Device property {name!r} is not declared.", node.targets[0])
    return ConfigureProperty(
        **context.metadata(node),
        resource_id=context.device_resource(reference).node_id,
        property_id=prop.semantic_id,
        value=expression(context, node.value, prop.type),
    )


def operation(context: LoweringContext, node: ast.Call) -> StartAgitation | StopAgitation | None:
    member = device_member(context, node.func)
    if member is None:
        return None
    reference, name = member
    contract = device_contract(reference.device_type)
    command = next((c for c in contract.operations if c.name == name), None)
    if command is None:
        context.fail("unsupported_operation", f"Device command {name!r} is not declared.", node)
    if command.semantic_id not in (START_AGITATION_ID, STOP_AGITATION_ID):
        context.fail("unsupported_operation", "Native device commands require the contribution stage.", node)
    if node.args or node.keywords:
        context.fail("operation_binding", f"{name} takes no arguments.", node)
    cls = StartAgitation if command.semantic_id == START_AGITATION_ID else StopAgitation
    return cls(**context.metadata(node), resource_id=context.device_resource(reference).node_id)
