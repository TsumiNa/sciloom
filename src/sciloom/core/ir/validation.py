"""Symbol, type and control-flow validation shared by every frontend."""

from dataclasses import replace

from sciloom.core.diagnostics import Diagnostic, IRValidationError
from .device_contracts import START_AGITATION_ID, STOP_AGITATION_ID
from .device_validation import is_agitator, members_for, query_members_for, validate_directory
from .expressions import ExpressionChecker
from .model import (
    Assignment,
    BinaryOp,
    CanWrite,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    FunctionIR,
    If,
    IsDevice,
    ListLiteral,
    ListSet,
    Literal,
    Node,
    Program,
    StartAgitation,
    Statement,
    StopAgitation,
    SupportsOperation,
    VariableRole,
    While,
)
from .schema import _convert
from .traversal import iter_nodes
from .types import ListType, ScalarType, ValueType, is_assignable


def validate(package: Program) -> tuple[Diagnostic, ...]:
    """Return errors without modifying IR. An empty tuple means valid v4 semantics.

    This does not prove Executor acceptance, loop termination or device safety.
    Programmatic construction and JSON import receive the same structural checks.
    """
    try:
        _convert(package, Program, "$", encode=True)
    except IRValidationError as error:
        return error.diagnostics
    except RecursionError:
        return (Diagnostic(code="ir_shape", message="IR is cyclic or nested too deeply.", path="$"),)

    errors: list[Diagnostic] = []

    def report(code: str, message: str, path: str, node: Node | None = None) -> None:
        errors.append(
            Diagnostic(
                code=code,
                message=message,
                path=path,
                node_id=node.node_id if node else None,
                source=node.source if node else None,
            )
        )

    if package.format_version != 4:
        report("format_version", "Only semantic format version 4 is supported.", "$.format_version")
    validate_directory(package, report)

    seen: dict[str, str] = {}
    for node, path in iter_nodes(package):
        if not node.node_id.strip():
            report("empty_id", "Semantic IDs must not be empty.", f"{path}.node_id", node)
        elif node.node_id in seen:
            report("duplicate_id", f"ID {node.node_id!r} already occurs at {seen[node.node_id]}.", path, node)
        else:
            seen[node.node_id] = path
        if node.source and (not node.source.path.strip() or node.source.line < 1 or node.source.column < 0):
            report("source_span", "Source needs a path, line >= 1 and column >= 0.", f"{path}.source", node)

    resources = {r.node_id: r for r in package.resources}
    logical_ids: set[str] = set()
    for i, resource in enumerate(package.resources):
        if not resource.logical_id.strip() or resource.logical_id in logical_ids:
            report(
                "resource_identity", "Logical resource IDs must be nonempty and unique.", f"$.resources[{i}]", resource
            )
        logical_ids.add(resource.logical_id)
    functions = {function.node_id: function for function in package.functions}
    symbols = {variable.node_id: variable for function in package.functions for variable in function.variables}
    if package.entry_function_id not in functions:
        report("entry_function", "Entry must reference a function in this package.", "$.entry_function_id")

    checker = ExpressionChecker(symbols, report)
    expression = checker.check

    def check_assignment(source: ValueType | None, target: ValueType | None, path: str, node: Node) -> None:
        if source is not None and target is not None and not is_assignable(source, target):
            report("type_mismatch", f"Cannot assign {source.value} to {target.value}.", path, node)

    def statements(
        body: tuple[Statement, ...], function: FunctionIR, path: str, narrowed: dict[str, str] | None = None
    ) -> None:
        narrowed = {} if narrowed is None else narrowed
        for i, stmt in enumerate(body):
            p = f"{path}[{i}]"
            if isinstance(stmt, Assignment):
                target = expression(stmt.target, function, f"{p}.target")
                source = expression(stmt.value, function, f"{p}.value")
                check_assignment(source, target, p, stmt)
            elif isinstance(stmt, ListSet):
                target = expression(stmt.target, function, f"{p}.target")
                index = expression(stmt.index, function, f"{p}.index")
                source = expression(stmt.value, function, f"{p}.value")
                if index is not None and index != ScalarType.INTEGER:
                    report("index_type", "List indices must be integers, excluding bool.", f"{p}.index", stmt.index)
                if target is not None and not isinstance(target, ListType):
                    report("list_type", "Indexed assignment requires a list variable.", p, stmt)
                if stmt.op is not None and stmt.op not in (
                    BinaryOp.ADD,
                    BinaryOp.SUBTRACT,
                    BinaryOp.MULTIPLY,
                    BinaryOp.DIVIDE,
                ):
                    report("operator_type", "Augmented index assignment requires an arithmetic operator.", p, stmt)
                elif isinstance(target, ListType):
                    if stmt.op is not None:
                        source = checker.binary(stmt.op, target.element_type, source, p, stmt)
                    check_assignment(source, target.element_type, p, stmt)
            elif isinstance(stmt, (If, While)):
                condition = expression(stmt.condition, function, f"{p}.condition")
                if condition is not None and condition != ScalarType.BOOLEAN:
                    report("condition_type", "Control-flow conditions must be boolean.", f"{p}.condition", stmt)
                if isinstance(stmt, If):
                    statements(stmt.then_body, function, f"{p}.then_body", narrowed)
                    statements(stmt.else_body, function, f"{p}.else_body", narrowed)
                else:
                    statements(stmt.body, function, f"{p}.body", narrowed)
            elif isinstance(stmt, (ConfigureProperty, StartAgitation, StopAgitation, DeviceCommand)):
                resource = resources.get(stmt.resource_id)
                if resource is not None and resource.node_id in narrowed:
                    resource = replace(resource, device_type_id=narrowed[resource.node_id])
                properties, commands = members_for(package, resource) if resource else ((), ())
                if resource is None:
                    report("unknown_resource", "Operation must reference a declared device.", p, stmt)
                if isinstance(stmt, ConfigureProperty):
                    prop = next((v for v in properties if v.semantic_id == stmt.property_id), None)
                    actual = expression(stmt.value, function, f"{p}.value")
                    if prop is None:
                        report(
                            "device_property",
                            "Property must have a declared signature for this device category.",
                            p,
                            stmt,
                        )
                    else:
                        check_assignment(actual, prop.type, p, stmt)
                elif isinstance(stmt, DeviceCommand):
                    if stmt.operation_id in (START_AGITATION_ID, STOP_AGITATION_ID):
                        report(
                            "device_command",
                            "Built-in agitation commands require their dedicated semantic nodes.",
                            p,
                            stmt,
                        )
                    command = next((c for c in commands if c.semantic_id == stmt.operation_id), None)
                    parameters = {v.name: v.type for v in command.parameters} if command else {}
                    names = [a.name for a in stmt.arguments]
                    if command is None or len(set(names)) != len(names) or set(names) != parameters.keys():
                        report("device_command", "Command arguments must match its declared signature.", p, stmt)
                    for argument in stmt.arguments:
                        check_assignment(
                            expression(argument.value, function, p), parameters.get(argument.name), p, stmt
                        )
                elif resource is not None and not is_agitator(package, resource):
                    report("device_type", "Agitation lifecycle requires an Agitator resource.", p, stmt)
            elif isinstance(stmt, DeviceIf):
                predicate = stmt.condition
                resource = resources.get(predicate.resource_id)
                if resource is not None and resource.node_id in narrowed:
                    resource = replace(resource, device_type_id=narrowed[resource.node_id])
                properties, commands = query_members_for(package, resource) if resource else ((), ())
                if resource is None:
                    report("unknown_resource", "Device predicate must reference a declared resource.", p, predicate)
                if isinstance(predicate, CanWrite):
                    if not any(v.semantic_id == predicate.property_id for v in properties):
                        report("device_property", "Device query must name a declared property.", p, predicate)
                elif isinstance(predicate, SupportsOperation):
                    if not any(v.semantic_id == predicate.operation_id for v in commands):
                        report("device_command", "Device query must name a declared command.", p, predicate)
                elif isinstance(predicate, IsDevice):
                    queried_type = next(
                        (c for c in package.device_types if c.type_id == predicate.device_type_id), None
                    )
                    current_type = next(
                        (
                            c
                            for c in package.device_types
                            if resource is not None and c.type_id == resource.device_type_id
                        ),
                        None,
                    )
                    if queried_type is None:
                        report("device_contract", "Device query must name a declared type.", p, predicate)
                    elif current_type is not None and not (
                        queried_type.type_id in (current_type.type_id, *current_type.base_type_ids)
                        or current_type.type_id in queried_type.base_type_ids
                    ):
                        report(
                            "device_condition",
                            "is_device requires a type on the current device interface's inheritance chain.",
                            p,
                            predicate,
                        )
                true_types = dict(narrowed)
                if isinstance(predicate, IsDevice) and resource is not None:
                    current_type = next((c for c in package.device_types if c.type_id == resource.device_type_id), None)
                    if current_type is None or predicate.device_type_id not in (
                        current_type.type_id,
                        *current_type.base_type_ids,
                    ):
                        true_types[predicate.resource_id] = predicate.device_type_id
                statements(stmt.then_body, function, f"{p}.then_body", true_types)
                statements(stmt.else_body, function, f"{p}.else_body", narrowed)
            else:
                callee = functions.get(stmt.function_id)
                if callee is None:
                    report("unknown_function", f"Unknown function {stmt.function_id!r}.", p, stmt)
                for label, role in (("inputs", VariableRole.INPUT), ("outputs", VariableRole.OUTPUT)):
                    expected = {v.node_id: v for v in callee.variables if v.role == role} if callee else {}
                    bound: set[str] = set()
                    for j, binding in enumerate(getattr(stmt, label)):
                        bp = f"{p}.{label}[{j}]"
                        expr = binding.value if label == "inputs" else binding.target
                        actual = expression(expr, function, f"{bp}.{'value' if label == 'inputs' else 'target'}")
                        if callee:
                            if binding.parameter_id not in expected or binding.parameter_id in bound:
                                report(
                                    "call_binding",
                                    "Binding must identify a unique callee parameter of the correct role.",
                                    bp,
                                    stmt,
                                )
                            else:
                                parameter_type = expected[binding.parameter_id].type
                                if label == "inputs":
                                    check_assignment(actual, parameter_type, bp, stmt)
                                else:
                                    check_assignment(parameter_type, actual, bp, stmt)
                        bound.add(binding.parameter_id)
                    if callee and (missing := set(expected) - bound):
                        report("call_binding", f"Missing {label}: {', '.join(sorted(missing))}.", f"{p}.{label}", stmt)

    for i, function in enumerate(package.functions):
        p = f"$.functions[{i}]"
        if not function.name.strip():
            report("empty_name", "Function name must not be empty.", f"{p}.name", function)
        names: set[str] = set()
        for j, variable in enumerate(function.variables):
            vp = f"{p}.variables[{j}]"
            if variable.owner_id != function.node_id:
                report("variable_owner", "Variable owner must match its containing function.", vp, variable)
            if not variable.name.strip() or variable.name in names:
                report("variable_name", "Variable names must be nonempty and unique within a function.", vp, variable)
            names.add(variable.name)
            if variable.initial is not None:
                if isinstance(variable.initial, ListLiteral) and any(
                    not isinstance(e, Literal) for e in variable.initial.elements
                ):
                    report("initializer_literal", "List initializers must contain only scalar literals.", vp, variable)
                if variable.role != VariableRole.INTERNAL:
                    report(
                        "initializer_role",
                        "Only internal variable initializers are supported in the current IR.",
                        vp,
                        variable,
                    )
                initial = expression(variable.initial, function, f"{vp}.initial")
                check_assignment(initial, variable.type, vp, variable)
            elif variable.role == VariableRole.INTERNAL:
                report(
                    "missing_initializer",
                    "Internal variables need an explicit literal initial value in the current IR.",
                    vp,
                    variable,
                )
        statements(function.body, function, f"{p}.body")

    return tuple(errors)
