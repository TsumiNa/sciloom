"""Build a validated Program from specialized Function instances."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import (
    FunctionIR,
    ListLiteral,
    ListType,
    Literal,
    Program,
    TimerResource,
    Variable,
    VariableRole,
    ZoneLiteral,
    ZoneType,
    validate,
)
from sciloom.core.locations import Zone
from sciloom.flow.device_slots import DeviceReference

# Function is read at runtime below, not only in annotations. Do not move this
# import behind TYPE_CHECKING: component_paths tests instances with isinstance.
from sciloom.flow.function import Function
from sciloom.units import Duration, RotationalSpeed, Temperature, TemperatureDifference, TemperatureRate, Volume
from .context import LoweringContext, ProgramScope
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
    scope = ProgramScope(paths=component_paths(root), instances=[root], ids={id(root): "fn:0"})
    functions: list[FunctionIR] = []
    index = 0
    while index < len(scope.instances):
        instance = scope.instances[index]
        context = LoweringContext(instance, scope.ids[id(instance)], scope)
        for name in instance.device_fields:
            reference = context.host_attribute(name)
            assert isinstance(reference, DeviceReference)
            context.device_resource(reference)
        for name in instance.timer_fields:
            identity = f"{context.function_id}:timer:{name}"
            scope.resources[identity] = TimerResource(node_id=identity, owner_id=context.function_id, name=name)
        function = _build_function(context)
        functions.append(function)
        index += 1
    package = Program(
        entry_function_id="fn:0",
        functions=tuple(functions),
        resources=tuple(scope.resources.values()),
        device_types=tuple(scope.device_types.values()),
    )
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return package


def _initial_scalar(
    value: bool
    | int
    | float
    | str
    | RotationalSpeed
    | Volume
    | Duration
    | Temperature
    | TemperatureDifference
    | TemperatureRate,
) -> bool | int | float | str:
    if isinstance(value, RotationalSpeed):
        return value.rps
    if isinstance(value, Volume):
        return value.m3
    if isinstance(value, Duration):
        return value.seconds
    if isinstance(value, (Temperature, TemperatureDifference)):
        return value.kelvin
    if isinstance(value, TemperatureRate):
        return value.kelvin_per_second
    return value


def _build_function(context: LoweringContext) -> FunctionIR:
    node = runtime_source(context)
    variables = []
    for field in context.instance.model_fields.values():
        initial: Literal | ListLiteral | ZoneLiteral | None = None
        if field.role == VariableRole.INTERNAL:
            if isinstance(field.type, ZoneType):
                assert isinstance(field.default, Zone)
                initial = ZoneLiteral(node_id=f"{context.symbol(field.name)}:initial", well_ids=field.default.well_ids)
            elif isinstance(field.type, ListType):
                assert isinstance(field.default, tuple)
                initial = ListLiteral(
                    node_id=f"{context.symbol(field.name)}:initial",
                    type=field.type,
                    elements=tuple(
                        Literal(
                            node_id=f"{context.symbol(field.name)}:initial:{i}",
                            type=field.type.element_type,
                            value=_initial_scalar(value),
                        )
                        for i, value in enumerate(field.default)
                    ),
                )
            else:
                initial = Literal(
                    node_id=f"{context.symbol(field.name)}:initial",
                    type=field.type,
                    value=_initial_scalar(
                        cast(
                            bool
                            | int
                            | float
                            | str
                            | RotationalSpeed
                            | Volume
                            | Duration
                            | Temperature
                            | TemperatureDifference
                            | TemperatureRate,
                            field.default,
                        )
                    ),
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
