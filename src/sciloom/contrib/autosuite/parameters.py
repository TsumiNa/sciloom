"""Encode Function parameter declarations and Execute Function bindings."""

from __future__ import annotations

from ...core.ir import Call, FunctionIR, VariableRole
from .context import CodegenContext
from .encoding import SCALARS
from .expressions import render_expression
from .xml import XmlNode, xml_node as _xml


def functiondata(context: CodegenContext, function: FunctionIR, call: Call | None = None) -> XmlNode:
    groups = []
    for tag, role in (("inputs", VariableRole.INPUT), ("outputs", VariableRole.OUTPUT)):
        parameters = [v for v in function.variables if v.role == role]
        entries = [_xml("count", str(len(parameters)))]
        inputs = {b.parameter_id: b.value for b in call.inputs} if call else {}
        outputs = {b.parameter_id: b.target for b in call.outputs} if call else {}
        for i, variable in enumerate(parameters):
            variable_name = context.names[variable.node_id]
            expression_text = ""
            if call and role == VariableRole.INPUT:
                variable_name = ""
                expression_text = render_expression(context, inputs[variable.node_id])
            elif call:
                variable_name = context.names[outputs[variable.node_id].symbol_id]
            entries.append(
                _xml(
                    f"item{i}",
                    "",
                    _xml("id", context.identifier("parameter", variable.node_id)),
                    _xml("name", variable.name),
                    _xml("variablename", variable_name),
                    _xml("variabletype", SCALARS[variable.type].parameter_type),
                    _xml("isarray", "0"),
                    _xml("expression", expression_text),
                )
            )
        entries.append(_xml("sortType", "0"))
        groups.append(_xml(tag, "", *entries))
    return _xml("functiondata", "", *groups)
