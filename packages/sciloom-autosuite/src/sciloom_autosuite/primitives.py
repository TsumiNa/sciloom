"""Observed Set Variable and Macro wire forms used by task/expression scheduling."""

from dataclasses import dataclass

from sciloom.core.ir import FunctionIR, Variable
from .context import CodegenContext
from .encoding import variable_declaration
from .xml import XmlNode, xml_node as _xml


@dataclass(frozen=True, kw_only=True)
class SequentialZone:
    """Observed one-source sequential selection; never exposed in Semantic IR."""

    source: str
    variable: Variable
    fragment_size: int = 1


def set_variable(
    context: CodegenContext,
    tag: str,
    name: str,
    expression: str,
    *,
    identity: str | None = None,
    array: bool = False,
    index: str = "",
) -> XmlNode:
    return _xml(
        tag,
        "",
        *context.metadata("Set Variable"),
        _xml("variablename", name),
        _xml("expressiontext", expression),
        _xml("elementselectmode", "4" if array else "0"),
        _xml("elementnumber", index),
        _xml("numberofelements"),
        _xml("startindex", "0"),
        _xml("clearvariable", "0"),
        _xml("sortwells", "0"),
        _xml("enumerationtype", "0"),
        _xml("wellsenumeration", "0"),
        _xml("elementsenumeration", "0"),
        _xml("id", context.identifier("statement", identity or context.fresh_id())),
        typeid="Chemspeed.SATaskSetVariable.1",
    )


def macro(
    context: CodegenContext,
    tag: str,
    identity: str,
    function: FunctionIR,
    body: tuple[XmlNode, ...],
    *,
    name: str = "Macro Task",
    condition_type: str = "0",
    condition: str = "",
    variables: tuple[Variable, ...] = (),
    branches: bool = False,
    role: str = "statement",
    sequential: SequentialZone | None = None,
) -> XmlNode:
    if sequential is not None:
        variables = (*variables, sequential.variable)
    declared = [variable_declaration(v, context.names[v.node_id]) for v in variables]
    occupied = {context.names[v.node_id] for v in (*function.variables, *context.temporaries[function.node_id])}
    occupied.update(context.parameter_names[v.node_id] for v in function.variables)
    occupied.update(context.names[v.node_id] for v in variables)
    loop_name, fragment_name = "loop", "fragment"
    while loop_name in occupied:
        loop_name += "_"
    while fragment_name in occupied:
        fragment_name += "_"
    return _xml(
        tag,
        "",
        *context.metadata(name, expanded=True),
        _xml("conditionloop", "1"),
        _xml("conditionif", condition if condition_type == "1" else ""),
        _xml("conditionwhile", condition if condition_type == "2" else ""),
        _xml("conditiontype", condition_type),
        _xml("loopvariable", loop_name),
        _xml("fragmentvariable", fragment_name),
        _xml("executionmode", "1" if sequential is not None else "0"),
        _xml("sequentialzones", "", _xml("count", "0"))
        if sequential is None
        else _xml(
            "sequentialzones",
            "",
            _xml("count", "1"),
            _xml(
                "sequentialzone0",
                "",
                _xml("fragmentsize", str(sequential.fragment_size)),
                _xml("variablename", context.names[sequential.variable.node_id]),
                _xml("zonename", sequential.source),
            ),
        ),
        _xml("multicondition", "1" if branches else "0"),
        _xml("multiloop", "0"),
        _xml("variables", "", *declared, sortingType="1"),
        _xml("id", context.identifier(role, identity)),
        _xml("tasks", "", *body),
        typeid="Chemspeed.SAMacroTask.1",
    )
