"""Quantity types survive Python, JSON and reference execution."""

import pytest

from sciloom import Duration, Function, Input, Output, RotationalSpeed, Var, Volume, minute, mL, rpm, runtime, s, uL
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json


class Quantities(Function):
    number: Input[float]
    supplied: Input[Volume]
    volumes: Input[list[Volume]]
    duration: Output[Duration]
    volume: Output[Volume]
    millilitres: Output[float]
    ratio: Output[float]
    copied: Output[list[Volume]]
    earlier: Output[bool]
    elapsed: Var[Duration] = 1 * minute
    changes: Var[list[Duration]] = [0 * s, -1 * s]

    @runtime
    def run(self) -> None:
        self.volume = self.number * mL + self.supplied
        self.millilitres = self.volume / mL
        self.ratio = self.volume / self.supplied
        self.duration = -self.elapsed + self.number * s
        self.earlier = self.duration < 0 * s
        self.copied = self.volumes
        self.copied[0] += 100 * uL
        self.elapsed += 1 * s


def test_quantities_python_json_and_persistent_state():
    program = Quantities().to_ir()
    inputs = {"number": 2.0, "supplied": 1 * mL, "volumes": [2 * mL]}
    for candidate in (program, from_json(to_json(program))):
        session = Interpreter(candidate)
        result = session.run(inputs=inputs)
        assert result.outputs["volume"].m3 == pytest.approx(3e-6)
        assert result.outputs["millilitres"] == pytest.approx(3)
        assert result.outputs["ratio"] == pytest.approx(3)
        assert result.outputs["duration"] == -58 * s
        assert result.outputs["earlier"] is True
        assert result.outputs["copied"][0].m3 == pytest.approx(2.1e-6)
        assert inputs["volumes"] == [2 * mL]
        assert session.run(inputs=inputs).outputs["duration"] == -59 * s
        assert result.outputs["duration"] == -58 * s


def test_speed_unit_runtime_construction_preserves_nonnegative_rule():
    class Speed(Function):
        number: Input[float]
        value: Output[RotationalSpeed]

        @runtime
        def run(self) -> None:
            self.value = self.number * rpm

    session = Interpreter(Speed().to_ir())
    assert session.run(inputs={"number": 600.0}).outputs["value"] == 600 * rpm
    with pytest.raises(ExecutionError, match="invalid_speed"):
        session.run(inputs={"number": -1.0})


def test_wrong_dimensions_are_rejected():
    class Bad(Function):
        volume: Input[Volume]
        time: Input[Duration]
        result: Output[Volume]

        @runtime
        def run(self) -> None:
            self.result = self.volume + self.time

    with pytest.raises(IRValidationError, match="operator_type"):
        Bad().to_ir()


def test_invalid_speed_intermediate_cannot_hide_inside_a_comparison():
    class BadIntermediate(Function):
        number: Input[float]
        result: Output[bool]

        @runtime
        def run(self) -> None:
            self.result = self.number * rpm == 0 * rpm

    with pytest.raises(ExecutionError, match="invalid_speed"):
        Interpreter(BadIntermediate().to_ir()).run(inputs={"number": -1.0})


def test_quantity_inputs_require_the_declared_dimension():
    program = Quantities().to_ir()
    for supplied in (1.0, 1 * s, True):
        with pytest.raises(ExecutionError, match="runtime_type"):
            Interpreter(program).run(inputs={"number": 1.0, "supplied": supplied, "volumes": [1 * mL]})


def test_quantity_defaults_require_the_declared_dimension():
    with pytest.raises(IRValidationError, match="class_schema"):

        class BadDefault(Function):
            amount: Var[Volume] = 1 * s

    with pytest.raises(IRValidationError, match="class_schema"):

        class BadListDefault(Function):
            intervals: Var[list[Duration]] = [1 * minute, 1 * mL]
