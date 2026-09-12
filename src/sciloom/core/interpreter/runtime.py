"""Execute typed IR directly; no source evaluation, code generation or vendor imports."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ...units import RotationalSpeed
from ..diagnostics import IRValidationError
from ..ir import Assignment, ListSet, SetAgitation, StopAgitation, Call, FunctionIR, If, Program, Reference, ScalarType, Statement, VariableRole, While, validate
from ..ir.model import Node

from .values import InputValue, OutputValue, RuntimeValue, checked_index, coerce, fail, initial_value, input_value, output_value
from .expressions import apply_binary, evaluate


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
    outputs: Mapping[str, OutputValue]
    state: Mapping[str, Mapping[str, RuntimeValue]]
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
        self._state: dict[str, dict[str, RuntimeValue]] = {f.node_id: {} for f in program.functions}
        self._steps = 0
        self._resources = {r.node_id: AgitationState() for r in program.resources}
        self._events: list[AgitationEvent] = []
        for variable in self._variables.values():
            if variable.role == VariableRole.INTERNAL:
                assert variable.initial is not None
                self._state[variable.owner_id][variable.node_id] = coerce(initial_value(variable.initial), variable.type, variable)

    def _tick(self, node: Node) -> None:
        self._steps += 1
        if self._steps > self.config.max_steps:
            fail("step_limit", "Reference execution exhausted its step budget.", node)

    def run(self, *, inputs: Mapping[str, InputValue] | None = None) -> ExecutionResult:
        entry = self._functions[self.program.entry_function_id]
        values = {} if inputs is None else dict(inputs)
        parameters = [v for v in entry.variables if v.role == VariableRole.INPUT]
        if set(values) != {v.name for v in parameters}:
            fail("input_binding", "Supply exactly the entry function's named inputs.", entry)
        arguments = {
            parameter.node_id: input_value(values[parameter.name], parameter.type, parameter)
            for parameter in parameters
        }
        self._steps = 0
        self._events = []
        try:
            outputs = self._call(entry, arguments, 1)
        except RecursionError:
            fail("execution_depth", "Reference evaluation exceeded the host nesting limit.")
        named = {
            v.name: output_value(outputs[v.node_id], v.type)
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

    def _read(self, reference: Reference, frame: dict[str, RuntimeValue]) -> RuntimeValue:
        variable = self._variables[reference.symbol_id]
        storage = self._state[variable.owner_id] if variable.role == VariableRole.INTERNAL else frame
        if variable.node_id not in storage:
            fail("uninitialized_read", f"Variable {variable.name!r} has no value in this call.", reference)
        return storage[variable.node_id]

    def _write(self, target: Reference, value: RuntimeValue, frame: dict[str, RuntimeValue]) -> None:
        variable = self._variables[target.symbol_id]
        storage = self._state[variable.owner_id] if variable.role == VariableRole.INTERNAL else frame
        storage[variable.node_id] = coerce(value, variable.type, target)

    def _call(self, function: FunctionIR, inputs: dict[str, RuntimeValue], depth: int) -> dict[str, RuntimeValue]:
        self._tick(function)
        if depth > self.config.max_call_depth:
            fail("call_depth", "Reference execution exceeded its call-depth budget.", function)
        frame = dict(inputs)
        self._statements(function.body, frame, depth)
        outputs = {}
        for variable in function.variables:
            if variable.role == VariableRole.OUTPUT:
                if variable.node_id not in frame:
                    fail("missing_output", f"Output {variable.name!r} was not assigned in this call.", variable)
                outputs[variable.node_id] = frame[variable.node_id]
        return outputs

    def _statements(self, statements: tuple[Statement, ...], frame: dict[str, RuntimeValue], depth: int) -> None:
        for statement in statements:
            self._tick(statement)
            if isinstance(statement, Assignment):
                self._write(statement.target, evaluate(self, statement.value, frame), frame)
            elif isinstance(statement, ListSet):
                # Plain assignment evaluates the RHS first. Augmented assignment
                # checks and reads the selected element before evaluating its RHS.
                value = evaluate(self, statement.value, frame) if statement.op is None else None
                values = self._read(statement.target, frame)
                assert isinstance(values, tuple)
                index = checked_index(values, evaluate(self, statement.index, frame), statement)
                if statement.op is not None:
                    value = apply_binary(statement.op, values[index], evaluate(self, statement.value, frame), statement)
                assert value is not None
                self._write(statement.target, values[:index] + (value,) + values[index + 1:], frame)
            elif isinstance(statement, If):
                branch = statement.then_body if evaluate(self, statement.condition, frame) else statement.else_body
                self._statements(branch, frame, depth)
            elif isinstance(statement, While):
                while evaluate(self, statement.condition, frame):
                    self._statements(statement.body, frame, depth)
            elif isinstance(statement, Call):
                callee = self._functions[statement.function_id]
                arguments = {
                    b.parameter_id: coerce(
                        evaluate(self, b.value, frame), self._variables[b.parameter_id].type, statement
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
                        rps=coerce(
                            evaluate(self, statement.speed, frame), ScalarType.ROTATIONAL_SPEED, statement
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
                fail("unsupported_operation", f"Cannot execute {type(statement).__name__}.", statement)
