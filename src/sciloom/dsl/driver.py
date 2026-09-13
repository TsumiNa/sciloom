"""Build a validated Program from specialized Function instances."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import (
    DeviceResource,
    DeviceTypeContract,
    FunctionIR,
    ListLiteral,
    ListType,
    Literal,
    Program,
    Variable,
    VariableRole,
    validate,
)
from sciloom.flow.device_slots import DeviceReference

# Function is read at runtime below, not only in annotations. Do not move this
# import behind TYPE_CHECKING: component_paths tests instances with isinstance.
from sciloom.flow.function import Function
from sciloom.units import RotationalSpeed
from .context import LoweringContext
from .source import runtime_source
from .statements import statements


def component_paths(root: Function) -> dict[int, str]:
    """Find stable host composition paths without invoking user descriptors."""
    paths = {id(root): ""}
    pending: list[object] = [root]
    for instance in pending:
        attributes: dict[str, object] = {}
        for cls in reversed(type(instance).__mro__):
            attributes.update(vars(cls))
        attributes.update(vars(instance))
        for name, value in sorted(attributes.items()):
            if isinstance(value, Function) and id(value) not in paths:
                if not name.isidentifier() or name.startswith("_"):
                    raise TypeError("Composed Function names must be public Python identifiers.")
                paths[id(value)] = ".".join(filter(None, (paths[id(instance)], name)))
                pending.append(value)
    return paths


def lower(root: Function) -> Program:
    """Build a deterministic package from source and scalar instance configuration."""
    instances: list[Function] = [root]
    ids = {id(root): "fn:0"}
    functions: list[FunctionIR] = []
    resources: dict[str, DeviceResource] = {}
    paths = component_paths(root)
    device_types: dict[str, DeviceTypeContract] = {}
    index = 0
    while index < len(instances):
        instance = instances[index]
        function_id = ids[id(instance)]
        context = LoweringContext(instance, function_id, instances, ids, resources, paths, device_types)
        for name in instance.device_fields:
            reference = context.host_attribute(name)
            assert isinstance(reference, DeviceReference)
            context.device_resource(reference)
        function = build_function(context)
        functions.append(function)
        index += 1
    package = Program(
        entry_function_id="fn:0",
        functions=tuple(functions),
        resources=tuple(resources.values()),
        device_types=tuple(device_types.values()),
    )
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return package


def build_function(context: LoweringContext) -> FunctionIR:
    node = runtime_source(context)
    variables = []
    for field in context.instance.model_fields.values():
        initial: Literal | ListLiteral | None = None
        if field.role == VariableRole.INTERNAL:
            if isinstance(field.type, ListType):
                assert isinstance(field.default, tuple)
                initial = ListLiteral(
                    node_id=f"{context.symbol(field.name)}:initial",
                    type=field.type,
                    elements=tuple(
                        Literal(
                            node_id=f"{context.symbol(field.name)}:initial:{i}",
                            type=field.type.element_type,
                            value=value.rps if isinstance(value, RotationalSpeed) else value,
                        )
                        for i, value in enumerate(field.default)
                    ),
                )
            else:
                initial = Literal(
                    node_id=f"{context.symbol(field.name)}:initial",
                    type=field.type,
                    value=field.default.rps
                    if isinstance(field.default, RotationalSpeed)
                    else cast(bool | int | float, field.default),
                )
        variables.append(
            Variable(
                node_id=context.symbol(field.name),
                owner_id=context.function_id,
                name=field.name,
                role=field.role,
                type=field.type,
                initial=initial,
            )
        )
    function = FunctionIR(
        node_id=context.function_id,
        name=type(context.instance).__name__,
        source=context.span(node),
        variables=tuple(variables),
    )
    context.function_schema = function
    return replace(function, body=statements(context, node.body))
