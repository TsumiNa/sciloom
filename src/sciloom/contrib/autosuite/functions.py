"""Package emitted tasks into function definitions and the ASFP envelope."""

from __future__ import annotations

from dataclasses import replace

from sciloom.core.ir import ListType, VariableRole
from .context import CodegenContext
from .device_state import initialize_device_outputs
from .parameters import functiondata
from .primitives import macro, set_variable
from .tasks import statements
from .xml import AutoSuiteVersion, SerializationIR, xml_node as _xml


def build_functions(context: CodegenContext, target: AutoSuiteVersion) -> SerializationIR:
    functions = []
    used_names: set[str] = set()
    for function in context.functions.values():
        name = function.name
        while name in used_names:
            name += "_"
        used_names.add(name)
        internal = tuple(v for v in function.variables if v.role == VariableRole.INTERNAL)
        before, after = list(initialize_device_outputs(context, function)), []
        for variable in function.variables:
            if not isinstance(variable.type, ListType) or variable.role == VariableRole.INTERNAL:
                continue
            public_name = context.parameter_names[variable.node_id]
            private_name = context.temporary(function, variable.type)
            context.names[variable.node_id] = private_name
            if variable.role == VariableRole.INPUT:
                before.append(set_variable(context, "task", private_name, public_name, array=True))
            else:
                after.append(set_variable(context, "task", public_name, private_name, array=True))
        # Schedule first so every target-private variable is known before declaring locals.
        tasks = (*before, *statements(context, function.body, function, "task"), *after)
        declarations = (*internal, *context.temporaries[function.node_id])
        body = (
            (macro(context, "component", function.node_id, function, tasks, variables=declarations, role="locals"),)
            if declarations
            else tuple(replace(task, tag="component") for task in tasks)
        )
        functions.append(
            _xml(
                "function",
                "",
                *context.metadata(name, expanded=True),
                functiondata(context, function),
                _xml("id", context.identifier("function", function.node_id)),
                _xml("components", "", *body),
                typeid="Chemspeed.SATaskFunctionDefinition.1",
            )
        )
    return SerializationIR(target=target, root=_xml("functions", "", *functions))
