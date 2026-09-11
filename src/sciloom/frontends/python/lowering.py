"""Restricted ordinary-file Python source → typed Function IR."""

import ast
import inspect
import tokenize
from collections.abc import Sequence
from typing import Any, NoReturn, cast

from .model import Agitator, Function
from ...units import RotationalSpeed, SpeedUnit
from ...ir import (
    Assignment,
    AgitatorResource,
    SetAgitation,
    StopAgitation,
    Binary,
    BinaryOp,
    Call,
    Diagnostic,
    Expression,
    FunctionIR,
    If,
    InputBinding,
    IRValidationError,
    Literal,
    OutputBinding,
    Program,
    Reference,
    ScalarType,
    SourceSpan,
    Statement,
    Unary,
    UnaryOp,
    Variable,
    VariableRole,
    While,
    validate,
)

_BINARY = {
    ast.Add: BinaryOp.ADD,
    ast.Sub: BinaryOp.SUBTRACT,
    ast.Mult: BinaryOp.MULTIPLY,
    ast.Div: BinaryOp.DIVIDE,
    ast.Eq: BinaryOp.EQUAL,
    ast.NotEq: BinaryOp.NOT_EQUAL,
    ast.Lt: BinaryOp.LESS,
    ast.LtE: BinaryOp.LESS_EQUAL,
    ast.Gt: BinaryOp.GREATER,
    ast.GtE: BinaryOp.GREATER_EQUAL,
    ast.And: BinaryOp.AND,
    ast.Or: BinaryOp.OR,
}
_UNARY = {ast.UAdd: UnaryOp.POSITIVE, ast.USub: UnaryOp.NEGATIVE, ast.Not: UnaryOp.NOT}
_MISSING = object()


def lower(root: Function) -> Program:
    """Build a deterministic package from source and scalar instance configuration."""
    instances: list[Function] = [root]
    ids = {id(root): "fn:0"}
    functions: list[FunctionIR] = []
    resources: dict[str, AgitatorResource] = {}
    index = 0
    while index < len(instances):
        instance = instances[index]
        function_id = ids[id(instance)]
        function = _FunctionLowerer(instance, function_id, instances, ids, resources).build()
        functions.append(function)
        index += 1
    package = Program(entry_function_id="fn:0", functions=tuple(functions), resources=tuple(resources.values()))
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return package


class _FunctionLowerer:
    def __init__(
        self,
        instance: Function,
        function_id: str,
        instances: list[Function],
        ids: dict[int, str],
        resources: dict[str, AgitatorResource],
    ):
        self.instance = instance
        self.function_id = function_id
        self.instances = instances
        self.ids = ids
        self.resources = resources
        self.unit_names: dict[str, SpeedUnit] = {}
        self.filename = ""
        self.sequence = 0

    def fail(self, code: str, message: str, node: ast.AST | None = None) -> NoReturn:
        source = self.span(node) if node is not None else None
        raise IRValidationError(
            (Diagnostic(code=code, message=message, path=f"$.python.{self.function_id}", source=source),)
        )

    def span(self, node: ast.AST) -> SourceSpan:
        location = cast(ast.expr | ast.stmt, node)
        return SourceSpan(path=self.filename, line=location.lineno, column=location.col_offset)

    def metadata(self, node: ast.AST) -> dict[str, Any]:
        self.sequence += 1
        return {"node_id": f"{self.function_id}:node:{self.sequence}", "source": self.span(node)}

    def symbol(self, name: str, function_id: str | None = None) -> str:
        return f"{function_id or self.function_id}:var:{name}"

    def build(self) -> FunctionIR:
        for name in self.instance.model_fields:
            if name in vars(self.instance):
                self.fail("runtime_field_write", f"Instance configuration shadows runtime field {name!r}.")
        members: dict[str, Any] = {}
        for cls in reversed(type(self.instance).__mro__):
            members.update(vars(cls))
        methods = [
            getattr(value, "__sciloom_runtime__")
            for value in members.values()
            if inspect.isfunction(value) and hasattr(value, "__sciloom_runtime__")
        ]
        if len(methods) != 1:
            self.fail("runtime_method", "A Function requires exactly one @runtime instance method.")
        method = methods[0]
        self.unit_names = {name: value for name, value in method.__globals__.items() if isinstance(value, SpeedUnit)}
        self.filename = method.__code__.co_filename
        if not self.filename.endswith(".py"):
            self.fail("source_unavailable", "Runtime source must come from an ordinary .py file.")
        try:
            with tokenize.open(self.filename) as source:
                module = ast.parse(source.read(), filename=self.filename)
        except (OSError, UnicodeError, SyntaxError) as error:
            self.fail("source_unavailable", f"Cannot read runtime source: {error}")
        candidates = [
            node
            for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == method.__name__
            and min([node.lineno, *(d.lineno for d in node.decorator_list)]) == method.__code__.co_firstlineno
        ]
        if len(candidates) != 1 or not isinstance(candidates[0], ast.FunctionDef):
            self.fail("source_unavailable", "Cannot locate one synchronous runtime method in its source file.")
        node = candidates[0]
        args = node.args
        if (
            len(args.args) != 1
            or args.args[0].arg != "self"
            or args.posonlyargs
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
            or args.defaults
        ):
            self.fail("python_subset", "Runtime methods take only self; declare Input fields on the class.", node)
        variables = []
        for field in self.instance.model_fields.values():
            initial = None
            if field.role == VariableRole.INTERNAL:
                initial = Literal(
                    node_id=f"{self.symbol(field.name)}:initial",
                    type=field.type,
                    value=field.default.rps
                    if isinstance(field.default, RotationalSpeed)
                    else cast(bool | int | float, field.default),
                )
            variables.append(
                Variable(
                    node_id=self.symbol(field.name),
                    owner_id=self.function_id,
                    name=field.name,
                    role=field.role,
                    type=field.type,
                    initial=initial,
                )
            )
        return FunctionIR(
            node_id=self.function_id,
            name=type(self.instance).__name__,
            source=self.span(node),
            variables=tuple(variables),
            body=self.statements(node.body),
        )

    def host_attribute(self, name: str) -> Any:
        if name in vars(self.instance):
            return vars(self.instance)[name]
        return inspect.getattr_static(type(self.instance), name, _MISSING)

    def target(self, node: ast.AST) -> Reference:
        if (
            not isinstance(node, ast.Attribute)
            or not isinstance(node.value, ast.Name)
            or node.value.id != "self"
            or node.attr not in self.instance.model_fields
        ):
            self.fail("runtime_field", "Assignment targets must be declared self.<runtime_field> references.", node)
        return Reference(**self.metadata(node), symbol_id=self.symbol(node.attr))

    def expression(self, node: ast.AST) -> Expression:
        if isinstance(node, ast.Constant):
            value = node.value
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in self.instance.model_fields:
                return Reference(**self.metadata(node), symbol_id=self.symbol(node.attr))
            value = self.host_attribute(node.attr)
        elif (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mult)
            and isinstance(node.right, ast.Name)
            and node.right.id in self.unit_names
        ):
            number = self.expression(node.left)
            if not isinstance(number, Literal) or number.type not in (ScalarType.INTEGER, ScalarType.REAL):
                self.fail(
                    "quantity_literal",
                    "Unit literals require a host numeric value; use Input[RotationalSpeed] for runtime inputs.",
                    node,
                )
            try:
                speed = self.unit_names[node.right.id].__rmul__(number.value)
            except (ValueError, TypeError) as error:
                self.fail("quantity_literal", str(error), node)
            return Literal(**self.metadata(node), type=ScalarType.ROTATIONAL_SPEED, value=speed.rps)
        elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            return Binary(
                **self.metadata(node),
                op=_BINARY[type(node.op)],
                left=self.expression(node.left),
                right=self.expression(node.right),
            )
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return Unary(**self.metadata(node), op=_UNARY[type(node.op)], operand=self.expression(node.operand))
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _BINARY:
            return Binary(
                **self.metadata(node),
                op=_BINARY[type(node.ops[0])],
                left=self.expression(node.left),
                right=self.expression(node.comparators[0]),
            )
        elif isinstance(node, ast.BoolOp):
            result = self.expression(node.values[0])
            for value_node in node.values[1:]:
                result = Binary(
                    **self.metadata(node), op=_BINARY[type(node.op)], left=result, right=self.expression(value_node)
                )
            return result
        else:
            self.fail("python_subset", f"Unsupported runtime expression: {type(node).__name__}.", node)
        if isinstance(value, RotationalSpeed):
            return Literal(**self.metadata(node), type=ScalarType.ROTATIONAL_SPEED, value=value.rps)
        scalar = {bool: ScalarType.BOOLEAN, int: ScalarType.INTEGER, float: ScalarType.REAL}.get(type(value))
        if scalar is None:
            self.fail("host_value", "Only scalar bool/int/float host values can enter runtime expressions.", node)
        return Literal(**self.metadata(node), type=scalar, value=cast(bool | int | float, value))

    def call(self, node: ast.Call, targets: Sequence[ast.expr]) -> Call:
        callee_node = node.func
        if (
            not isinstance(callee_node, ast.Attribute)
            or not isinstance(callee_node.value, ast.Name)
            or callee_node.value.id != "self"
        ):
            self.fail("python_subset", "Only calls to composed self.<function> instances are supported.", node)
        callee = self.host_attribute(callee_node.attr)
        if not isinstance(callee, Function):
            self.fail("python_subset", "Runtime calls require a Function instance composed before compilation.", node)
        if id(callee) not in self.ids:
            self.ids[id(callee)] = f"fn:{len(self.instances)}"
            self.instances.append(callee)
        callee_id = self.ids[id(callee)]
        inputs = [field for field in callee.model_fields.values() if field.role == VariableRole.INPUT]
        outputs = [field for field in callee.model_fields.values() if field.role == VariableRole.OUTPUT]
        if len(node.args) > len(inputs) or len(targets) != len(outputs):
            self.fail("call_binding", "Call arity or assigned output count does not match the callee schema.", node)
        bound = {field.name: arg for field, arg in zip(inputs, node.args)}
        input_names = {field.name for field in inputs}
        for keyword in node.keywords:
            if keyword.arg not in input_names or keyword.arg in bound:
                self.fail("call_binding", "Unknown, duplicate or unpacked input argument.", node)
            bound[keyword.arg] = keyword.value
        if set(bound) != input_names:
            self.fail("call_binding", "Every callee input must be bound exactly once.", node)
        return Call(
            **self.metadata(node),
            function_id=callee_id,
            inputs=tuple(
                InputBinding(parameter_id=self.symbol(field.name, callee_id), value=self.expression(bound[field.name]))
                for field in inputs
            ),
            outputs=tuple(
                OutputBinding(parameter_id=self.symbol(field.name, callee_id), target=self.target(target))
                for field, target in zip(outputs, targets)
            ),
        )

    def operation(self, node: ast.Call) -> SetAgitation | StopAgitation | None:
        method = node.func
        if not (
            isinstance(method, ast.Attribute)
            and isinstance(method.value, ast.Attribute)
            and isinstance(method.value.value, ast.Name)
            and method.value.value.id == "self"
        ):
            return None
        component = self.host_attribute(method.value.attr)
        if not isinstance(component, Agitator):
            return None
        if method.attr == "set_speed":
            if len(node.args) == 1 and not node.keywords:
                speed = self.expression(node.args[0])
            elif not node.args and len(node.keywords) == 1 and node.keywords[0].arg == "speed":
                speed = self.expression(node.keywords[0].value)
            else:
                self.fail("operation_binding", "set_speed requires exactly one speed argument.", node)
        elif method.attr == "stop":
            if node.args or node.keywords:
                self.fail("operation_binding", "stop takes no arguments.", node)
        else:
            self.fail("unsupported_operation", f"Unknown agitator operation {method.attr!r}.", node)
        resource = self.resources.setdefault(
            component.resource_id,
            AgitatorResource(node_id=f"resource:{component.resource_id}", logical_id=component.resource_id),
        )
        if method.attr == "set_speed":
            return SetAgitation(**self.metadata(node), resource_id=resource.node_id, speed=speed)
        return StopAgitation(**self.metadata(node), resource_id=resource.node_id)

    def statements(self, body: list[ast.stmt]) -> tuple[Statement, ...]:
        statements: list[Statement] = []
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
                    statements.append(self.call(node.value, targets))
                else:
                    statements.append(
                        Assignment(**self.metadata(node), target=self.target(target), value=self.expression(node.value))
                    )
            elif isinstance(node, ast.AugAssign) and type(node.op) in _BINARY:
                statements.append(
                    Assignment(
                        **self.metadata(node),
                        target=self.target(node.target),
                        value=Binary(
                            **self.metadata(node),
                            op=_BINARY[type(node.op)],
                            left=self.expression(node.target),
                            right=self.expression(node.value),
                        ),
                    )
                )
            elif isinstance(node, ast.If):
                statements.append(
                    If(
                        **self.metadata(node),
                        condition=self.expression(node.test),
                        then_body=self.statements(node.body),
                        else_body=self.statements(node.orelse),
                    )
                )
            elif isinstance(node, ast.While) and not node.orelse:
                statements.append(
                    While(**self.metadata(node), condition=self.expression(node.test), body=self.statements(node.body))
                )
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                operation = self.operation(node.value)
                statements.append(operation if operation is not None else self.call(node.value, []))
            else:
                self.fail("python_subset", f"Unsupported runtime statement: {type(node).__name__}.", node)
        return tuple(statements)
