"""Recognize trusted predicate markers and lower both typed device branches."""

import ast
import inspect

from sciloom.core.ir import CanWrite, DeviceIf, IsDevice, SupportsOperation
from sciloom.devices import BaseDevice
from sciloom.devices.declarations import device_contract
from . import comptime
from .context import LoweringContext
from .device_schema import DeviceReference


def static_object(context: LoweringContext, node: ast.AST) -> object:
    """Resolve names/static attributes without evaluating host calls/descriptors."""
    if isinstance(node, ast.Name):
        return context.static_names.get(node.id)
    if isinstance(node, ast.Attribute):
        return inspect.getattr_static(static_object(context, node.value), node.attr, None)
    return None


def device_if(context: LoweringContext, node: ast.If) -> DeviceIf | None:
    from .statements import statements

    call = node.test
    if not isinstance(call, ast.Call):
        return None
    marker = static_object(context, call.func)
    if not any(marker is query for query in (comptime.can_write, comptime.supports, comptime.is_device)):
        return None
    if len(call.args) != 2 or call.keywords:
        context.fail("device_condition", "Device queries require two positional arguments.", call)
    receiver = call.args[0]
    if not (
        isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name) and receiver.value.id == "self"
    ):
        context.fail("device_condition", "Device queries require a declared self.<device> slot.", receiver)
    reference = context.host_attribute(receiver.attr)
    if not isinstance(reference, DeviceReference):
        context.fail("device_condition", "Device query receiver is not a declared device slot.", receiver)
    resource_id = context.device_resource(reference).node_id
    declared = context.device_type(reference)
    narrowed = None
    condition: CanWrite | SupportsOperation | IsDevice
    if marker is comptime.is_device:
        cls = static_object(context, call.args[1])
        if not isinstance(cls, type) or not issubclass(cls, BaseDevice):
            context.fail("device_condition", "is_device requires a declared device class.", call.args[1])
        if not (issubclass(cls, declared) or issubclass(declared, cls)):
            context.fail(
                "device_condition",
                "is_device requires a type on the current device interface's inheritance chain.",
                call.args[1],
            )
        context.register_device_type(cls)
        condition = IsDevice(**context.metadata(call), resource_id=resource_id, device_type_id=cls.device_type_id)
        narrowed = declared if issubclass(declared, cls) else cls
    elif marker is comptime.supports:
        member = call.args[1]
        if not isinstance(member, ast.Attribute):
            context.fail("device_condition", "supports requires a registered DeviceType.command declaration.", member)
        owner = static_object(context, member.value)
        if not isinstance(owner, type) or not issubclass(owner, BaseDevice):
            context.fail("device_condition", "supports requires a registered device command.", member)
        contract = device_contract(owner)
        command = next((c for c in contract.operations if c.name == member.attr), None)
        if command is None:
            context.fail("device_condition", "supports accepts commands, not properties or getters.", member)
        context.register_device_type(owner)
        condition = SupportsOperation(
            **context.metadata(call), resource_id=resource_id, operation_id=command.semantic_id
        )
    else:
        name = call.args[1]
        if not isinstance(name, ast.Constant) or not isinstance(name.value, str):
            context.fail("device_condition", "can_write requires a declared property name as a string literal.", name)
        candidates = [
            declared,
            *(
                value
                for value in context.static_names.values()
                if isinstance(value, type) and issubclass(value, declared)
            ),
        ]
        matches = {}
        for cls in candidates:
            contract = device_contract(cls)
            for prop in contract.properties:
                if prop.name == name.value:
                    matches[prop.semantic_id] = prop
                    context.register_device_type(cls)
        if len(matches) != 1:
            context.fail(
                "device_condition",
                "can_write needs one unambiguous property declared by a compatible device type in scope.",
                name,
            )
        condition = CanWrite(**context.metadata(call), resource_id=resource_id, property_id=next(iter(matches)))

    metadata = context.metadata(node)
    original = context.narrowed_devices.copy()
    try:
        if narrowed is not None:
            context.narrowed_devices[resource_id] = narrowed
        then_body = statements(context, node.body)
    finally:
        context.narrowed_devices = original
    return DeviceIf(**metadata, condition=condition, then_body=then_body, else_body=statements(context, node.orelse))
