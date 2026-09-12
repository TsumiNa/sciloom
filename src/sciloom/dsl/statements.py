"""Lower calls, domain operations and structured runtime statements."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from .context import LoweringContext
from .expressions import BINARY_OPERATORS, expression, is_length_call
from .model import Function
from .device_operations import configure, device_member, operation
from ..core.ir import Assignment, Binary, Call, If, InputBinding, ListSet, ListType, OutputBinding, Reference, ScalarType, Statement, VariableRole, While


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
            InputBinding(parameter_id=context.symbol(field.name, callee_id), value=expression(context, bound[field.name], field.type))
            for field in inputs
        ),
        outputs=tuple(
            OutputBinding(parameter_id=context.symbol(field.name, callee_id), target=context.target(target))
            for field, target in zip(outputs, targets)
        ),
    )


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
            configuration = configure(context, node)
            if configuration is not None:
                result.append(configuration)
                continue
            target = node.targets[0]
            if isinstance(node.value, ast.Call) and not is_length_call(node.value):
                if isinstance(target, ast.Subscript):
                    context.fail("call_binding", "Function outputs must bind to whole variables, not indexed elements.", target)
                targets = list(target.elts) if isinstance(target, ast.Tuple) else [target]
                result.append(call(context, node.value, targets))
            elif isinstance(target, ast.Subscript):
                destination, element_type = indexed_target(context, target)
                result.append(ListSet(**context.metadata(node), target=destination, index=expression(context, target.slice), value=expression(context, node.value, element_type)))
            else:
                metadata = context.metadata(node)
                destination = context.target(target)
                result.append(
                    Assignment(**metadata, target=destination, value=expression(context, node.value, context.type_of(destination)))
                )
        elif isinstance(node, ast.AugAssign) and type(node.op) in BINARY_OPERATORS:
            if device_member(context, node.target) is not None:
                context.fail("device_property_read", "Device properties only support plain assignment.", node)
            if isinstance(node.target, ast.Subscript):
                destination, element_type = indexed_target(context, node.target)
                result.append(ListSet(**context.metadata(node), target=destination, index=expression(context, node.target.slice), value=expression(context, node.value, element_type), op=BINARY_OPERATORS[type(node.op)]))
                continue
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


def indexed_target(context: LoweringContext, node: ast.Subscript) -> tuple[Reference, ScalarType]:
    if device_member(context, node.value) is not None:
        context.fail("device_property_read", "Indexed device-property updates require getters, which are unsupported.", node)
    if isinstance(node.slice, ast.Slice):
        context.fail("python_subset", "List slicing is unsupported.", node)
    destination = context.target(node.value)
    value_type = context.type_of(destination)
    if not isinstance(value_type, ListType):
        context.fail("list_type", "Indexed assignment requires a declared list variable.", node)
    return destination, value_type.element_type
