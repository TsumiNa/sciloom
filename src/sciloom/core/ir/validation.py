"""Symbol, type and control-flow validation shared by every frontend."""

from .schema import _convert
from .expressions import ExpressionChecker
from .types import is_assignable
from .traversal import iter_nodes
from ..diagnostics import Diagnostic, IRValidationError
from .model import Assignment, SetAgitation, StopAgitation, FunctionIR, If, Node, Program, ScalarType, Statement, VariableRole, While


def validate(package: Program) -> tuple[Diagnostic, ...]:
    """Return errors without modifying IR. An empty tuple means valid v2 semantics.

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

    if package.format_version != 2:
        report("format_version", "Only semantic format version 2 is supported.", "$.format_version")

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

    expression = ExpressionChecker(symbols, report).check

    def check_assignment(source: ScalarType | None, target: ScalarType | None, path: str, node: Node) -> None:
        if source is not None and target is not None and not is_assignable(source, target):
            report("type_mismatch", f"Cannot assign {source.value} to {target.value}.", path, node)

    def statements(body: tuple[Statement, ...], function: FunctionIR, path: str) -> None:
        for i, stmt in enumerate(body):
            p = f"{path}[{i}]"
            if isinstance(stmt, Assignment):
                target = expression(stmt.target, function, f"{p}.target")
                source = expression(stmt.value, function, f"{p}.value")
                check_assignment(source, target, p, stmt)
            elif isinstance(stmt, (If, While)):
                condition = expression(stmt.condition, function, f"{p}.condition")
                if condition is not None and condition != ScalarType.BOOLEAN:
                    report("condition_type", "Control-flow conditions must be boolean.", f"{p}.condition", stmt)
                if isinstance(stmt, If):
                    statements(stmt.then_body, function, f"{p}.then_body")
                    statements(stmt.else_body, function, f"{p}.else_body")
                else:
                    statements(stmt.body, function, f"{p}.body")
            elif isinstance(stmt, (SetAgitation, StopAgitation)):
                if stmt.resource_id not in resources:
                    report("unknown_resource", "Operation must reference a declared agitator.", p, stmt)
                if isinstance(stmt, SetAgitation):
                    speed_type = expression(stmt.speed, function, f"{p}.speed")
                    if speed_type is not None and speed_type != ScalarType.ROTATIONAL_SPEED:
                        report("quantity_type", "Agitation requires a rotational-speed quantity.", p, stmt)
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
