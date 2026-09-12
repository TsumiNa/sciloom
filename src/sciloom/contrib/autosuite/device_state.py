"""Thread target-private device configuration through normal Function returns."""

from dataclasses import dataclass, replace

from ...core.ir import Call, ConfigureProperty, FunctionIR, ScalarType, StartAgitation, Variable, VariableRole
from ...core.ir.traversal import iter_nodes
from .context import CodegenContext
from .primitives import set_variable
from .xml import XmlNode


@dataclass(frozen=True, kw_only=True)
class DeviceStorage:
    name: str
    input_id: str | None = None
    output_id: str | None = None


def prepare_device_state(context: CodegenContext) -> None:
    """Add private transport records without changing either public semantic IR."""
    dependencies = {
        f.node_id: {n.resource_id for n, _ in iter_nodes(f) if isinstance(n, (ConfigureProperty, StartAgitation))}
        for f in context.package.functions
    }
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
        storage: dict[str, DeviceStorage] = {}
        for resource_id in sorted(dependencies[function.node_id]):
            if function.node_id == context.package.entry_function_id:
                # Wire zeros only allocate storage; core's definite-configuration
                # proof prevents treating that initializer as semantic configuration.
                storage[resource_id] = DeviceStorage(name=context.temporary(function, ScalarType.ROTATIONAL_SPEED))
                continue
            parameters = []
            for role in (VariableRole.INPUT, VariableRole.OUTPUT):
                identity = context.fresh_id()
                name = f"sciloom_device_{context.sequence}_{role.value}"
                while name in context.parameter_names.values():
                    name += "_"
                parameter = Variable(node_id=identity, owner_id=function.node_id, name=name, role=role, type=ScalarType.ROTATIONAL_SPEED)
                parameters.append(parameter)
                context.variables[identity] = parameter
                context.names[identity] = name
                context.parameter_names[identity] = name
            function = replace(function, variables=(*function.variables, *parameters))
            storage[resource_id] = DeviceStorage(
                name=parameters[1].name, input_id=parameters[0].node_id, output_id=parameters[1].node_id,
            )
        context.functions[function.node_id] = function
        context.device_state[function.node_id] = storage


def initialize_device_outputs(context: CodegenContext, function: FunctionIR) -> tuple[XmlNode, ...]:
    """An unchanged branch must still return the incoming configuration value."""
    return tuple(
        set_variable(context, "task", storage.name, context.parameter_names[storage.input_id])
        for storage in context.device_state[function.node_id].values()
        if storage.input_id is not None
    )
