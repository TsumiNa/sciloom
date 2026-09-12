"""Lower calls, domain operations and structured runtime statements."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from .context import LoweringContext
from .expressions import BINARY_OPERATORS, expression
from .model import Agitator, Function
from ..core.ir import Assignment, AgitatorResource, SetAgitation, StopAgitation, Binary, Call, If, InputBinding, OutputBinding, Statement, VariableRole, While


def call(context: LoweringContext, node: ast.Call, targets: Sequence[ast.expr]) -> Call:
    callee_node = node.func
    if (
        not isinstance(callee_node, ast.Attribute)
        or not isinstance(callee_node.value, ast.Name)
        or callee_node.value.id != "self"
    ):
        context.fail("python_subset", "Only calls to composed self.<function> instances are supported.", node)
    callee = context.host_attribute(callee_node.attr)
    if not isinstance(callee, Function):
        context.fail("python_subset", "Runtime calls require a Function instance composed before compilation.", node)
    if id(callee) not in context.ids:
        context.ids[id(callee)] = f"fn:{len(context.instances)}"
        context.instances.append(callee)
    callee_id = context.ids[id(callee)]
    inputs = [field for field in callee.model_fields.values() if field.role == VariableRole.INPUT]
    outputs = [field for field in callee.model_fields.values() if field.role == VariableRole.OUTPUT]
    if len(node.args) > len(inputs) or len(targets) != len(outputs):
        context.fail("call_binding", "Call arity or assigned output count does not match the callee schema.", node)
    bound = {field.name: arg for field, arg in zip(inputs, node.args)}
    input_names = {field.name for field in inputs}
    for keyword in node.keywords:
        if keyword.arg not in input_names or keyword.arg in bound:
            context.fail("call_binding", "Unknown, duplicate or unpacked input argument.", node)
        bound[keyword.arg] = keyword.value
    if set(bound) != input_names:
        context.fail("call_binding", "Every callee input must be bound exactly once.", node)
    return Call(
        **context.metadata(node),
        function_id=callee_id,
        inputs=tuple(
            InputBinding(parameter_id=context.symbol(field.name, callee_id), value=expression(context, bound[field.name]))
            for field in inputs
        ),
        outputs=tuple(
            OutputBinding(parameter_id=context.symbol(field.name, callee_id), target=context.target(target))
            for field, target in zip(outputs, targets)
        ),
    )


def operation(context: LoweringContext, node: ast.Call) -> SetAgitation | StopAgitation | None:
    method = node.func
    if not (
        isinstance(method, ast.Attribute)
        and isinstance(method.value, ast.Attribute)
        and isinstance(method.value.value, ast.Name)
        and method.value.value.id == "self"
    ):
        return None
    component = context.host_attribute(method.value.attr)
    if not isinstance(component, Agitator):
        return None
    if method.attr == "set_speed":
        if len(node.args) == 1 and not node.keywords:
            speed = expression(context, node.args[0])
        elif not node.args and len(node.keywords) == 1 and node.keywords[0].arg == "speed":
            speed = expression(context, node.keywords[0].value)
        else:
            context.fail("operation_binding", "set_speed requires exactly one speed argument.", node)
    elif method.attr == "stop":
        if node.args or node.keywords:
            context.fail("operation_binding", "stop takes no arguments.", node)
    else:
        context.fail("unsupported_operation", f"Unknown agitator operation {method.attr!r}.", node)
    resource = context.resources.setdefault(
        component.resource_id,
        AgitatorResource(node_id=f"resource:{component.resource_id}", logical_id=component.resource_id),
    )
    if method.attr == "set_speed":
        return SetAgitation(**context.metadata(node), resource_id=resource.node_id, speed=speed)
    return StopAgitation(**context.metadata(node), resource_id=resource.node_id)


def statements(context: LoweringContext, body: list[ast.stmt]) -> tuple[Statement, ...]:
    result: list[Statement] = []
    for node in body:
        if isinstance(node, ast.Pass):
            continue
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(node.value, ast.Call):
                targets = list(target.elts) if isinstance(target, ast.Tuple) else [target]
                result.append(call(context, node.value, targets))
            else:
                result.append(
                    Assignment(**context.metadata(node), target=context.target(target), value=expression(context, node.value))
                )
        elif isinstance(node, ast.AugAssign) and type(node.op) in BINARY_OPERATORS:
            result.append(
                Assignment(
                    **context.metadata(node),
                    target=context.target(node.target),
                    value=Binary(
                        **context.metadata(node),
                        op=BINARY_OPERATORS[type(node.op)],
                        left=expression(context, node.target),
                        right=expression(context, node.value),
                    ),
                )
            )
        elif isinstance(node, ast.If):
            result.append(
                If(
                    **context.metadata(node),
                    condition=expression(context, node.test),
                    then_body=statements(context, node.body),
                    else_body=statements(context, node.orelse),
                )
            )
        elif isinstance(node, ast.While) and not node.orelse:
            result.append(
                While(**context.metadata(node), condition=expression(context, node.test), body=statements(context, node.body))
            )
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            domain_operation = operation(context, node.value)
            result.append(domain_operation if domain_operation is not None else call(context, node.value, []))
        else:
            context.fail("python_subset", f"Unsupported runtime statement: {type(node).__name__}.", node)
    return tuple(result)
