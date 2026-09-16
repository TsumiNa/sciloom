"""Lower calls, domain operations and structured runtime statements."""

from __future__ import annotations

import ast
from collections.abc import Sequence

from sciloom.core.ir import (
    Assignment,
    Binary,
    Call,
    DeviceIf,
    If,
    InputBinding,
    ListSet,
    ListType,
    LogValue,
    Notify,
    OutputBinding,
    ReadWallTime,
    Reference,
    ScalarType,
    Statement,
    VariableRole,
    While,
)

# Function is read at runtime below, not only in annotations. Do not move this
# import behind TYPE_CHECKING: composed calls test the callee with isinstance.
from sciloom.flow.function import Function
from sciloom.flow.logging import log
from sciloom.flow.messages import notify
from sciloom.flow.timing import now_text
from .context import LoweringContext
from .csv_append import csv_append
from .csv_read import csv_read
from .device_conditions import device_condition
from .device_operations import configure, device_command
from .expressions import BINARY_OPERATORS, expression, is_expression_call
from .timing import timing_statement


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
    if id(callee) not in context.scope.ids:
        context.scope.ids[id(callee)] = f"fn:{len(context.scope.instances)}"
        context.scope.instances.append(callee)
    callee_id = context.scope.ids[id(callee)]
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
            InputBinding(
                parameter_id=context.symbol(field.name, callee_id),
                value=expression(context, bound[field.name], field.type),
            )
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
        appended = csv_append(context, node)
        if appended is not None:
            result.append(appended)
            continue
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            read = csv_read(context, node)
            if read is not None:
                result.append(read)
                continue
            if isinstance(node.value, ast.Call) and context.static_object(node.value.func) is now_text:
                invocation = node.value
                if len(invocation.args) == 1 and not invocation.keywords:
                    format_node = invocation.args[0]
                elif not invocation.args and len(invocation.keywords) == 1 and invocation.keywords[0].arg == "format":
                    format_node = invocation.keywords[0].value
                else:
                    context.fail("call_binding", "now_text requires exactly one constant format argument.", invocation)
                format_value: object
                if isinstance(format_node, ast.Constant):
                    format_value = format_node.value
                elif (
                    isinstance(format_node, ast.Attribute)
                    and isinstance(format_node.value, ast.Name)
                    and format_node.value.id == "self"
                    and format_node.attr not in context.instance.model_fields
                ):
                    format_value = context.host_attribute(format_node.attr)
                else:
                    format_value = context.static_object(format_node)
                if not isinstance(format_value, str):
                    context.fail(
                        "wall_time_format", "now_text format must be host-time text, not a runtime value.", format_node
                    )
                result.append(
                    ReadWallTime(
                        **context.metadata(invocation),
                        target=context.target(node.targets[0]),
                        format=format_value,
                    )
                )
                continue
            configuration = configure(context, node)
            if configuration is not None:
                result.append(configuration)
                continue
            target = node.targets[0]
            if isinstance(node.value, ast.Call) and not is_expression_call(context, node.value):
                if isinstance(target, ast.Subscript):
                    context.fail(
                        "call_binding", "Function outputs must bind to whole variables, not indexed elements.", target
                    )
                targets = list(target.elts) if isinstance(target, ast.Tuple) else [target]
                result.append(call(context, node.value, targets))
            elif isinstance(target, ast.Subscript):
                destination, element_type = _indexed_target(context, target)
                result.append(
                    ListSet(
                        **context.metadata(node),
                        target=destination,
                        index=expression(context, target.slice),
                        value=expression(context, node.value, element_type),
                    )
                )
            else:
                metadata = context.metadata(node)
                destination = context.target(target)
                result.append(
                    Assignment(
                        **metadata,
                        target=destination,
                        value=expression(context, node.value, context.type_of(destination)),
                    )
                )
        elif isinstance(node, ast.AugAssign) and type(node.op) in BINARY_OPERATORS:
            if context.device_member(node.target) is not None:
                context.fail("device_property_read", "Device properties only support plain assignment.", node)
            if isinstance(node.target, ast.Subscript):
                destination, element_type = _indexed_target(context, node.target)
                result.append(
                    ListSet(
                        **context.metadata(node),
                        target=destination,
                        index=expression(context, node.target.slice),
                        value=expression(context, node.value, element_type),
                        op=BINARY_OPERATORS[type(node.op)],
                    )
                )
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
            query = device_condition(context, node)
            if query is not None:
                metadata = context.metadata(node)
                with context.narrowing(query.resource_id, query.narrowed_type):
                    then_body = statements(context, node.body)
                result.append(
                    DeviceIf(
                        **metadata,
                        condition=query.predicate,
                        then_body=then_body,
                        else_body=statements(context, node.orelse),
                    )
                )
                continue
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
                While(
                    **context.metadata(node),
                    condition=expression(context, node.test),
                    body=statements(context, node.body),
                )
            )
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            timed = timing_statement(context, node.value)
            if timed is not None:
                result.append(timed)
                continue
            if context.static_object(node.value.func) is now_text:
                context.fail("external_operation", "Assign now_text(...) to one declared text field.", node.value)
            if context.static_object(node.value.func) is notify:
                invocation = node.value
                if len(invocation.args) == 1 and not invocation.keywords:
                    message = invocation.args[0]
                elif not invocation.args and len(invocation.keywords) == 1 and invocation.keywords[0].arg == "message":
                    message = invocation.keywords[0].value
                else:
                    context.fail("call_binding", "notify requires exactly one message argument.", invocation)
                if isinstance(message, ast.Starred):
                    context.fail("call_binding", "notify does not support unpacked arguments.", invocation)
                result.append(
                    Notify(**context.metadata(invocation), message=expression(context, message, ScalarType.TEXT))
                )
                continue
            if context.static_object(node.value.func) is log:
                invocation = node.value
                names = [keyword.arg for keyword in invocation.keywords]
                if (
                    len(invocation.args) != 1
                    or isinstance(invocation.args[0], ast.Starred)
                    or len(names) != 2
                    or set(names) != {"category", "stream"}
                ):
                    context.fail(
                        "call_binding", "log requires one positional value and category/stream keywords.", invocation
                    )
                keywords = {keyword.arg: keyword.value for keyword in invocation.keywords}
                result.append(
                    LogValue(
                        **context.metadata(invocation),
                        value=expression(context, invocation.args[0]),
                        category=expression(context, keywords["category"], ScalarType.TEXT),
                        stream=expression(context, keywords["stream"], ScalarType.TEXT),
                    )
                )
                continue
            domain_operation = device_command(context, node.value)
            result.append(domain_operation if domain_operation is not None else call(context, node.value, []))
        else:
            context.fail("python_subset", f"Unsupported runtime statement: {type(node).__name__}.", node)
    return tuple(result)


def _indexed_target(context: LoweringContext, node: ast.Subscript) -> tuple[Reference, ScalarType]:
    if context.device_member(node.value) is not None:
        context.fail(
            "device_property_read", "Indexed device-property updates require getters, which are unsupported.", node
        )
    if isinstance(node.slice, ast.Slice):
        context.fail("python_subset", "List slicing is unsupported.", node)
    destination = context.target(node.value)
    value_type = context.type_of(destination)
    if not isinstance(value_type, ListType):
        context.fail("list_type", "Indexed assignment requires a declared list variable.", node)
    return destination, value_type.element_type
