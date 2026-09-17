"""Thread target-private device configuration through normal Function returns."""

from dataclasses import dataclass, replace

from sciloom.core.ir import (
    Call,
    ConfigureProperty,
    FunctionIR,
    ListType,
    ScalarType,
    StartAgitation,
    Variable,
    VariableRole,
)
from sciloom.core.ir.device_contracts import AGITATION_SPEED_ID
from sciloom.core.ir.traversal import iter_nodes
from .context import CodegenContext
from .primitives import set_variable
from .xml import XmlNode


@dataclass(frozen=True, kw_only=True)
class DeviceStorage:
    name: str
    type: ScalarType | ListType
    input_id: str | None = None
    output_id: str | None = None


def prepare_device_state(context: CodegenContext) -> None:
    """Add private transport records without changing either public semantic IR."""
    dependencies = {
        f.node_id: {
            (n.resource_id, n.property_id if isinstance(n, ConfigureProperty) else AGITATION_SPEED_ID)
            for n, _ in iter_nodes(f)
            if isinstance(n, (ConfigureProperty, StartAgitation))
        }
        for f in context.package.functions
    }
    property_types = {p.semantic_id: p.type for c in context.package.device_types for p in c.properties}
    changed = True
    while changed:
        changed = False
        for function in context.package.functions:
            required = dependencies[function.node_id]
            before = len(required)
            for node, _ in iter_nodes(function):
                if isinstance(node, Call):
                    required.update(dependencies[node.function_id])
            changed |= before != len(required)

    for original in context.package.functions:
        function = original
        storage: dict[tuple[str, str], DeviceStorage] = {}
        for key in sorted(dependencies[function.node_id]):
            value_type = property_types[key[1]]
            if function.node_id == context.package.entry_function_id:
                # Wire zeros only allocate storage; core's definite-configuration
                # proof prevents treating that initializer as semantic configuration.
                storage[key] = DeviceStorage(name=context.temporary(function, value_type), type=value_type)
                continue
            parameters = []
            for role in (VariableRole.INPUT, VariableRole.OUTPUT):
                identity = context.fresh_id()
                name = f"sciloom_device_{context.sequence}_{role.value}"
                while name in context.parameter_names.values():
                    name += "_"
                parameter = Variable(node_id=identity, owner_id=function.node_id, name=name, role=role, type=value_type)
                parameters.append(parameter)
                context.variables[identity] = parameter
                context.names[identity] = name
                context.parameter_names[identity] = name
            function = replace(function, variables=(*function.variables, *parameters))
            storage[key] = DeviceStorage(
                name=parameters[1].name,
                type=value_type,
                input_id=parameters[0].node_id,
                output_id=parameters[1].node_id,
            )
        context.functions[function.node_id] = function
        context.device_state[function.node_id] = storage


def initialize_device_outputs(context: CodegenContext, function: FunctionIR) -> tuple[XmlNode, ...]:
    """An unchanged branch must still return the incoming configuration value."""
    return tuple(
        set_variable(
            context,
            "task",
            storage.name,
            context.parameter_names[storage.input_id],
            array=isinstance(storage.type, ListType),
        )
        for storage in context.device_state[function.node_id].values()
        if storage.input_id is not None
    )
