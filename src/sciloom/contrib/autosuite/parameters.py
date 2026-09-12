"""Encode parameter declarations and already-evaluated call bindings."""

from ...core.ir import FunctionIR, ListType, VariableRole
from .context import CodegenContext
from .encoding import SCALARS
from .xml import XmlNode, xml_node as _xml


def functiondata(
    context: CodegenContext,
    function: FunctionIR,
    *,
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
) -> XmlNode:
    groups = []
    for tag, role in (("inputs", VariableRole.INPUT), ("outputs", VariableRole.OUTPUT)):
        parameters = [v for v in function.variables if v.role == role]
        entries = [_xml("count", str(len(parameters)))]
        for i, variable in enumerate(parameters):
            array = isinstance(variable.type, ListType)
            scalar = variable.type.element_type if isinstance(variable.type, ListType) else variable.type
            variable_name = context.parameter_names[variable.node_id]
            expression_text = ""
            if inputs is not None and role == VariableRole.INPUT:
                variable_name = inputs[variable.node_id] if array else ""
                expression_text = "" if array else inputs[variable.node_id]
            elif outputs is not None and role == VariableRole.OUTPUT:
                variable_name = outputs[variable.node_id]
            entries.append(
                _xml(
                    f"item{i}",
                    "",
                    _xml("id", context.identifier("parameter", variable.node_id)),
                    _xml("name", variable.name),
                    _xml("variablename", variable_name),
                    _xml("variabletype", SCALARS[scalar].parameter_type),
                    _xml("isarray", "1" if array else "0"),
                    _xml("expression", expression_text),
                )
            )
        entries.append(_xml("sortType", "0"))
        groups.append(_xml(tag, "", *entries))
    return _xml("functiondata", "", *groups)
