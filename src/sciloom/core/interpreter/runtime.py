"""Execute typed IR directly; no source evaluation, code generation or vendor imports."""

import math
import operator
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import NoReturn

from ...units import RotationalSpeed
from ..diagnostics import Diagnostic, ExecutionError, IRValidationError
from ..ir import (
    Assignment,
    SetAgitation,
    StopAgitation,
    BinaryOp,
    Call,
    Expression,
    FunctionIR,
    If,
    Literal,
    Program,
    Reference,
    ScalarType,
    Statement,
    Unary,
    UnaryOp,
    VariableRole,
    While,
    validate,
)
from ..ir.model import Node

ScalarValue = bool | int | float
InputValue = ScalarValue | RotationalSpeed


@dataclass(frozen=True, kw_only=True)
class ExecutionConfig:
    max_steps: int = 10_000
    max_call_depth: int = 64

    def __post_init__(self) -> None:
        if type(self.max_steps) is not int or self.max_steps < 1:
            raise ValueError("max_steps must be a positive integer.")
        if type(self.max_call_depth) is not int or not 1 <= self.max_call_depth <= 100:
            raise ValueError("max_call_depth must be an integer between 1 and 100.")


@dataclass(frozen=True, kw_only=True)
class AgitationState:
    enabled: bool = False
    speed: RotationalSpeed | None = None


@dataclass(frozen=True, kw_only=True)
class AgitationEvent:
    node_id: str
    resource_id: str
    enabled: bool
    speed: RotationalSpeed | None


@dataclass(frozen=True, kw_only=True)
class ExecutionResult:
    outputs: Mapping[str, InputValue]
    state: Mapping[str, Mapping[str, ScalarValue]]
    steps: int
    resources: Mapping[str, AgitationState]
    events: tuple[AgitationEvent, ...]


class Interpreter:
    """A session owns persistent internal state; each run gets fresh call frames.

    On failure, earlier state writes remain visible to subsequent runs. This is
    sequential execution, not a transactional rollback or physical simulator.
    """

    def __init__(self, program: Program, *, config: ExecutionConfig | None = None):
        diagnostics = validate(program)
        if diagnostics:
            raise IRValidationError(diagnostics)
        self.program = program
        self.config = config if config is not None else ExecutionConfig()
        self._functions = {f.node_id: f for f in program.functions}
        self._variables = {v.node_id: v for f in program.functions for v in f.variables}
        self._state: dict[str, dict[str, ScalarValue]] = {f.node_id: {} for f in program.functions}
        self._steps = 0
        self._resources = {r.node_id: AgitationState() for r in program.resources}
        self._events: list[AgitationEvent] = []
        for variable in self._variables.values():
            if variable.role == VariableRole.INTERNAL:
                assert variable.initial is not None
                self._state[variable.owner_id][variable.node_id] = self._coerce(
                    variable.initial.value, variable.type, variable
                )

    def _fail(self, code: str, message: str, node: Node | None = None) -> NoReturn:
        raise ExecutionError(
            (
                Diagnostic(
                    code=code,
                    message=message,
                    path="$.execution",
                    node_id=node.node_id if node else None,
                    source=node.source if node else None,
                ),
            )
        )

    def _tick(self, node: Node) -> None:
        self._steps += 1
        if self._steps > self.config.max_steps:
            self._fail("step_limit", "Reference execution exhausted its step budget.", node)

    def _coerce(self, value: ScalarValue, scalar: ScalarType, node: Node) -> ScalarValue:
        allowed = {
            ScalarType.INTEGER: (int,),
            ScalarType.REAL: (int, float),
            ScalarType.BOOLEAN: (bool,),
            ScalarType.ROTATIONAL_SPEED: (int, float),
        }[scalar]
        if type(value) not in allowed:
            self._fail("runtime_type", f"Expected {scalar.value}, received {type(value).__name__}.", node)
        try:
            result = float(value) if scalar in (ScalarType.REAL, ScalarType.ROTATIONAL_SPEED) else value
        except OverflowError:
            self._fail("numeric_error", "Value cannot be represented as a finite real.", node)
        if isinstance(result, float) and not math.isfinite(result):
            self._fail("numeric_error", "Nonfinite real value.", node)
        if scalar == ScalarType.ROTATIONAL_SPEED and result < 0:
            self._fail("invalid_speed", "Rotational speed must be nonnegative.", node)
        return result

    def run(self, *, inputs: Mapping[str, InputValue] | None = None) -> ExecutionResult:
        entry = self._functions[self.program.entry_function_id]
        values = {} if inputs is None else dict(inputs)
        parameters = [v for v in entry.variables if v.role == VariableRole.INPUT]
        if set(values) != {v.name for v in parameters}:
            self._fail("input_binding", "Supply exactly the entry function's named inputs.", entry)
        arguments = {}
        for parameter in parameters:
            value = values[parameter.name]
            if parameter.type == ScalarType.ROTATIONAL_SPEED:
                if not isinstance(value, RotationalSpeed):
                    self._fail(
                        "runtime_type", "A rotational-speed input requires a quantity such as 600 * rpm.", parameter
                    )
                value = value.rps
            elif isinstance(value, RotationalSpeed):
                self._fail("runtime_type", "A quantity cannot be passed to a scalar input.", parameter)
            arguments[parameter.node_id] = self._coerce(value, parameter.type, parameter)
        self._steps = 0
        self._events = []
        try:
            outputs = self._call(entry, arguments, 1)
        except RecursionError:
            self._fail("execution_depth", "Reference evaluation exceeded the host nesting limit.")
        named = {
            v.name: (
                RotationalSpeed(rps=outputs[v.node_id]) if v.type == ScalarType.ROTATIONAL_SPEED else outputs[v.node_id]
            )
            for v in entry.variables
            if v.role == VariableRole.OUTPUT
        }
        snapshot = {key: MappingProxyType(dict(value)) for key, value in self._state.items()}
        return ExecutionResult(
            outputs=MappingProxyType(named),
            state=MappingProxyType(snapshot),
            steps=self._steps,
            resources=MappingProxyType(dict(self._resources)),
            events=tuple(self._events),
        )

    def _read(self, reference: Reference, frame: dict[str, ScalarValue]) -> ScalarValue:
        variable = self._variables[reference.symbol_id]
        storage = self._state[variable.owner_id] if variable.role == VariableRole.INTERNAL else frame
        if variable.node_id not in storage:
            self._fail("uninitialized_read", f"Variable {variable.name!r} has no value in this call.", reference)
        return storage[variable.node_id]

    def _write(self, target: Reference, value: ScalarValue, frame: dict[str, ScalarValue]) -> None:
        variable = self._variables[target.symbol_id]
        storage = self._state[variable.owner_id] if variable.role == VariableRole.INTERNAL else frame
        storage[variable.node_id] = self._coerce(value, variable.type, target)

    def _expression(self, expression: Expression, frame: dict[str, ScalarValue]) -> ScalarValue:
        self._tick(expression)
        if isinstance(expression, Literal):
            return self._coerce(expression.value, expression.type, expression)
        if isinstance(expression, Reference):
            return self._read(expression, frame)
        result: ScalarValue
        try:
            if isinstance(expression, Unary):
                value = self._expression(expression.operand, frame)
                if expression.op == UnaryOp.NOT:
                    result = not value
                elif expression.op == UnaryOp.POSITIVE:
                    result = +value
                else:
                    result = -value
            else:
                left = self._expression(expression.left, frame)
                if expression.op == BinaryOp.AND and not left:
                    return False
                if expression.op == BinaryOp.OR and left:
                    return True
                right = self._expression(expression.right, frame)
                result = {
                    BinaryOp.ADD: operator.add,
                    BinaryOp.SUBTRACT: operator.sub,
                    BinaryOp.MULTIPLY: operator.mul,
                    BinaryOp.DIVIDE: operator.truediv,
                    BinaryOp.EQUAL: operator.eq,
                    BinaryOp.NOT_EQUAL: operator.ne,
                    BinaryOp.LESS: operator.lt,
                    BinaryOp.LESS_EQUAL: operator.le,
                    BinaryOp.GREATER: operator.gt,
                    BinaryOp.GREATER_EQUAL: operator.ge,
                    BinaryOp.AND: operator.and_,
                    BinaryOp.OR: operator.or_,
                }[expression.op](left, right)
        except (ZeroDivisionError, OverflowError) as error:
            self._fail("numeric_error", str(error), expression)
        if isinstance(result, float) and not math.isfinite(result):
            self._fail("numeric_error", "Arithmetic produced a nonfinite value.", expression)
        return result

    def _call(self, function: FunctionIR, inputs: dict[str, ScalarValue], depth: int) -> dict[str, ScalarValue]:
        self._tick(function)
        if depth > self.config.max_call_depth:
            self._fail("call_depth", "Reference execution exceeded its call-depth budget.", function)
        frame = dict(inputs)
        self._statements(function.body, frame, depth)
        outputs = {}
        for variable in function.variables:
            if variable.role == VariableRole.OUTPUT:
                if variable.node_id not in frame:
                    self._fail("missing_output", f"Output {variable.name!r} was not assigned in this call.", variable)
                outputs[variable.node_id] = frame[variable.node_id]
        return outputs

    def _statements(self, statements: tuple[Statement, ...], frame: dict[str, ScalarValue], depth: int) -> None:
        for statement in statements:
            self._tick(statement)
            if isinstance(statement, Assignment):
                self._write(statement.target, self._expression(statement.value, frame), frame)
            elif isinstance(statement, If):
                branch = statement.then_body if self._expression(statement.condition, frame) else statement.else_body
                self._statements(branch, frame, depth)
            elif isinstance(statement, While):
                while self._expression(statement.condition, frame):
                    self._statements(statement.body, frame, depth)
            elif isinstance(statement, Call):
                callee = self._functions[statement.function_id]
                arguments = {
                    b.parameter_id: self._coerce(
                        self._expression(b.value, frame), self._variables[b.parameter_id].type, statement
                    )
                    for b in statement.inputs
                }
                outputs = self._call(callee, arguments, depth + 1)
                for binding in statement.outputs:
                    self._write(binding.target, outputs[binding.parameter_id], frame)
            elif isinstance(statement, (SetAgitation, StopAgitation)):
                previous = self._resources[statement.resource_id]
                if isinstance(statement, SetAgitation):
                    speed = RotationalSpeed(
                        rps=self._coerce(
                            self._expression(statement.speed, frame), ScalarType.ROTATIONAL_SPEED, statement
                        )
                    )
                    state = AgitationState(enabled=True, speed=speed)
                else:
                    state = AgitationState(enabled=False, speed=previous.speed)
                self._resources[statement.resource_id] = state
                self._events.append(
                    AgitationEvent(
                        node_id=statement.node_id,
                        resource_id=statement.resource_id,
                        enabled=state.enabled,
                        speed=state.speed,
                    )
                )
            else:
                self._fail("unsupported_operation", f"Cannot execute {type(statement).__name__}.", statement)
