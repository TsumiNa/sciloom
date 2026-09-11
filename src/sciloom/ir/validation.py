"""Symbol, type and control-flow validation shared by every frontend."""


from .codec import _convert
from .traversal import iter_nodes
from ..diagnostics import Diagnostic, IRValidationError
from .model import (
    Assignment,
    BinaryOp,
    Expression,
    FunctionIR,
    If,
    Literal,
    Node,
    Package,
    Reference,
    ScalarType,
    Statement,
    Unary,
    UnaryOp,
    VariableRole,
    While,
)


def _assignable(source: ScalarType, target: ScalarType) -> bool:
    return source == target or (source == ScalarType.INTEGER and target == ScalarType.REAL)


def validate(package: Package) -> tuple[Diagnostic, ...]:
    """Return errors without modifying IR. An empty tuple means valid v1 semantics.

    This does not prove Executor acceptance, loop termination or device safety.
    Programmatic construction and JSON import receive the same structural checks.
    """
    try:
        _convert(package, Package, "$", encode=True)
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

    if package.format_version != 1:
        report("format_version", "Only semantic format version 1 is supported.", "$.format_version")

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

    functions = {function.node_id: function for function in package.functions}
    symbols = {variable.node_id: variable for function in package.functions for variable in function.variables}
    if package.entry_function_id not in functions:
        report("entry_function", "Entry must reference a function in this package.", "$.entry_function_id")

    def expression(expr: Expression, function: FunctionIR, path: str) -> ScalarType | None:
        if isinstance(expr, Literal):
            valid = {
                ScalarType.INTEGER: type(expr.value) is int,
                ScalarType.REAL: type(expr.value) in (int, float),
                ScalarType.BOOLEAN: type(expr.value) is bool,
            }[expr.type]
            if not valid:
                report("literal_type", f"Value does not represent {expr.type.value}.", path, expr)
                return None
            return expr.type
        if isinstance(expr, Reference):
            variable = symbols.get(expr.symbol_id)
            if variable is None:
                report("unknown_symbol", f"Unknown variable {expr.symbol_id!r}.", path, expr)
                return None
            if variable.owner_id != function.node_id or variable not in function.variables:
                report(
                    "symbol_scope", "Variable belongs to a different function; globals are not implicit.", path, expr
                )
                return None
            return variable.type
        if isinstance(expr, Unary):
            operand = expression(expr.operand, function, f"{path}.operand")
            if operand is None:
                return None
            if expr.op == UnaryOp.NOT:
                if operand == ScalarType.BOOLEAN:
                    return ScalarType.BOOLEAN
            elif operand in (ScalarType.INTEGER, ScalarType.REAL):
                return operand
            report("operator_type", f"Operator {expr.op.value!r} cannot take {operand.value}.", path, expr)
            return None
        left = expression(expr.left, function, f"{path}.left")
        right = expression(expr.right, function, f"{path}.right")
        if left is None or right is None:
            return None
        numeric = left in (ScalarType.INTEGER, ScalarType.REAL) and right in (ScalarType.INTEGER, ScalarType.REAL)
        if expr.op in (BinaryOp.AND, BinaryOp.OR):
            if left == right == ScalarType.BOOLEAN:
                return ScalarType.BOOLEAN
        elif expr.op in (BinaryOp.EQUAL, BinaryOp.NOT_EQUAL):
            if left == right or numeric:
                return ScalarType.BOOLEAN
        elif expr.op in (BinaryOp.LESS, BinaryOp.LESS_EQUAL, BinaryOp.GREATER, BinaryOp.GREATER_EQUAL):
            if numeric:
                return ScalarType.BOOLEAN
        elif numeric:
            return (
                ScalarType.REAL
                if expr.op == BinaryOp.DIVIDE or ScalarType.REAL in (left, right)
                else ScalarType.INTEGER
            )
        report(
            "operator_type", f"Operator {expr.op.value!r} cannot combine {left.value} and {right.value}.", path, expr
        )
        return None

    def check_assignment(source: ScalarType | None, target: ScalarType | None, path: str, node: Node) -> None:
        if source is not None and target is not None and not _assignable(source, target):
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
                    report("initializer_role", "Only internal variable initializers are supported in v1.", vp, variable)
                initial = expression(variable.initial, function, f"{vp}.initial")
                check_assignment(initial, variable.type, vp, variable)
            elif variable.role == VariableRole.INTERNAL:
                report(
                    "missing_initializer",
                    "Internal variables need an explicit literal initial value in v1.",
                    vp,
                    variable,
                )
        statements(function.body, function, f"{p}.body")

    return tuple(errors)
