"""Organize runtime statements, Macro control flow and domain tasks."""

from __future__ import annotations

from ...core.diagnostics import CompilationError, Diagnostic
from ...core.ir import Assignment, Call, FunctionIR, If, SetAgitation, StopAgitation, Statement, Variable, While
from .agitation import agitation_task
from .context import CodegenContext
from .encoding import variable_declaration
from .expressions import render_expression
from .parameters import functiondata
from .xml import XmlNode, xml_node as _xml


def macro(
    context: CodegenContext,
    tag: str,
    identity: str,
    function: FunctionIR,
    body: tuple[Statement, ...],
    *,
    name: str = "Macro Task",
    condition_type: str = "0",
    condition: str = "",
    variables: tuple[Variable, ...] = (),
    branches: tuple[XmlNode, ...] = (),
    role: str = "statement",
) -> XmlNode:
    declared = [variable_declaration(v, context.names[v.node_id]) for v in variables]
    occupied = {context.names[v.node_id] for v in function.variables}
    loop_name, fragment_name = "loop", "fragment"
    while loop_name in occupied:
        loop_name += "_"
    while fragment_name in occupied:
        fragment_name += "_"
    children = [
        *context.metadata(name, expanded=True),
        _xml("conditionloop", "1"),
        _xml("conditionif", condition if condition_type == "1" else ""),
        _xml("conditionwhile", condition if condition_type == "2" else ""),
        _xml("conditiontype", condition_type),
        _xml("loopvariable", loop_name),
        _xml("fragmentvariable", fragment_name),
        _xml("executionmode", "0"),
        _xml("sequentialzones", "", _xml("count", "0")),
        _xml("multicondition", "1" if branches else "0"),
        _xml("multiloop", "0"),
        _xml("variables", "", *declared, sortingType="1"),
        _xml("id", context.identifier(role, identity)),
        _xml("tasks", "", *(branches or statements(context, body, function, "task"))),
    ]
    return _xml(tag, "", *children, typeid="Chemspeed.SAMacroTask.1")


def statements(context: CodegenContext, body: tuple[Statement, ...], function: FunctionIR, tag: str) -> tuple[XmlNode, ...]:
    result = []
    for statement in body:
        if isinstance(statement, Assignment):
            children = [
                *context.metadata("Set Variable"),
                _xml("variablename", context.names[statement.target.symbol_id]),
                _xml("expressiontext", render_expression(context, statement.value)),
                _xml("elementselectmode", "0"),
                _xml("elementnumber"),
                _xml("numberofelements"),
                _xml("startindex", "0"),
                _xml("clearvariable", "0"),
                _xml("sortwells", "0"),
                _xml("enumerationtype", "0"),
                _xml("wellsenumeration", "0"),
                _xml("elementsenumeration", "0"),
                _xml("id", context.identifier("statement", statement.node_id)),
            ]
            result.append(_xml(tag, "", *children, typeid="Chemspeed.SATaskSetVariable.1"))
        elif isinstance(statement, (SetAgitation, StopAgitation)):
            result.append(
                agitation_task(
                    tag=tag,
                    binding=context.resources[statement.resource_id],
                    speed=render_expression(context, statement.speed) if isinstance(statement, SetAgitation) else None,
                    identifier=context.identifier("statement", statement.node_id),
                )
            )
        elif isinstance(statement, Call):
            result.append(
                _xml(
                    tag,
                    "",
                    *context.metadata("Execute Function"),
                    functiondata(context, context.functions[statement.function_id], statement),
                    _xml("functionid", context.identifier("function", statement.function_id)),
                    _xml("id", context.identifier("statement", statement.node_id)),
                    typeid="Chemspeed.SATaskExecuteFunction.1",
                )
            )
        elif isinstance(statement, While):
            result.append(
                macro(context, 
                    tag,
                    statement.node_id,
                    function,
                    statement.body,
                    name="While",
                    condition_type="2",
                    condition=render_expression(context, statement.condition),
                )
            )
        elif isinstance(statement, If) and not statement.else_body:
            result.append(
                macro(context, 
                    tag,
                    statement.node_id,
                    function,
                    statement.then_body,
                    name="If",
                    condition_type="1",
                    condition=render_expression(context, statement.condition),
                )
            )
        elif isinstance(statement, If):
            branches = []
            for label, condition_type, condition, branch_body in (
                ("If", "0", render_expression(context, statement.condition), statement.then_body),
                ("Else", "2", "", statement.else_body),
            ):
                branches.append(
                    _xml(
                        "task",
                        "",
                        *context.metadata(label, expanded=True),
                        _xml("conditiontype", condition_type),
                        _xml("condition", condition),
                        _xml("id", context.identifier(label, statement.node_id)),
                        _xml("components", "", *statements(context, branch_body, function, "component")),
                        typeid="Chemspeed.SATaskCondition.1",
                    )
                )
            result.append(
                macro(context, tag, statement.node_id, function, (), name="If-Else", branches=tuple(branches))
            )
        else:
            raise CompilationError(
                (
                    Diagnostic(
                        code="unsupported_operation",
                        message=f"AutoSuite cannot emit {type(statement).__name__}.",
                        path="$",
                        node_id=statement.node_id,
                        source=statement.source,
                    ),
                )
            )
    return tuple(result)
