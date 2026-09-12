"""Package emitted tasks into function definitions and the ASFP envelope."""

from __future__ import annotations

from ...core.ir import VariableRole
from .context import CodegenContext
from .parameters import functiondata
from .tasks import macro, statements
from .xml import AutoSuiteVersion, SerializationIR, xml_node as _xml


def build_functions(context: CodegenContext, target: AutoSuiteVersion) -> SerializationIR:
    functions = []
    used_names: set[str] = set()
    for function in context.package.functions:
        name = function.name
        while name in used_names:
            name += "_"
        used_names.add(name)
        internal = tuple(v for v in function.variables if v.role == VariableRole.INTERNAL)
        body = (
            (macro(context, "component", function.node_id, function, function.body, variables=internal, role="locals"),)
            if internal
            else statements(context, function.body, function, "component")
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
