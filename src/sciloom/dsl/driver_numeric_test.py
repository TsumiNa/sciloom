"""Known numeric calls preserve Python result types and rounding semantics."""

import builtins
import math
from math import floor as lower_integer

import pytest

from sciloom import Duration, Function, Input, Output, Volume, mL, runtime, s
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json


class NumericValues(Function):
    value: Input[float]
    magnitude: Output[float]
    lower: Output[int]
    nearest: Output[int]

    @runtime
    def run(self) -> None:
        self.magnitude = abs(self.value)
        self.lower = lower_integer(self.value)
        self.nearest = round(self.value)


@pytest.mark.parametrize("value", [-3.5, -2.5, -1.2, -0.5, -0.0, 0.5, 1.5, 2.5, 3.5, 1e100])
def test_numeric_python_and_json(value):
    program = NumericValues().to_ir()
    for candidate in (program, from_json(to_json(program))):
        result = Interpreter(candidate).run(inputs={"value": value})
        assert result.outputs == {"magnitude": abs(value), "lower": math.floor(value), "nearest": round(value)}
        assert type(result.outputs["lower"]) is int
        assert type(result.outputs["nearest"]) is int


def test_integer_operations_do_not_round_through_float():
    integer_round = builtins.round

    class Integers(Function):
        value: Input[int]
        absolute: Output[int]
        lower: Output[int]
        nearest: Output[int]

        @runtime
        def run(self) -> None:
            self.absolute = builtins.abs(self.value)
            self.lower = math.floor(self.value)
            self.nearest = integer_round(self.value)

    value = -(10**100 + 1)
    assert Interpreter(Integers().to_ir()).run(inputs={"value": value}).outputs == {
        "absolute": -value,
        "lower": value,
        "nearest": value,
    }


def test_signed_quantity_magnitude_and_explicit_conversion():
    class Magnitudes(Function):
        amount: Input[Volume]
        interval: Input[Duration]
        volume: Output[Volume]
        duration: Output[Duration]
        whole_ml: Output[int]

        @runtime
        def run(self) -> None:
            self.volume = abs(self.amount)
            self.duration = abs(self.interval)
            self.whole_ml = math.floor(self.amount / mL)

    result = Interpreter(Magnitudes().to_ir()).run(inputs={"amount": -1.25 * mL, "interval": -2 * s})
    assert result.outputs == {"volume": 1.25 * mL, "duration": 2 * s, "whole_ml": -2}
    assert abs(-1.25 * mL) == 1.25 * mL
    assert abs(-2 * s) == 2 * s


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True])
def test_numeric_inputs_reject_nonfinite_and_boolean(value):
    with pytest.raises(ExecutionError):
        Interpreter(NumericValues().to_ir()).run(inputs={"value": value})


def test_shadowed_numeric_names_are_not_executed():
    def round(value):
        raise AssertionError("Source analysis must not call this function.")

    class Shadowed(Function):
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = round(2.5)

    with pytest.raises(IRValidationError):
        Shadowed().to_ir()


def test_numeric_calls_reject_lists():
    class ListMagnitude(Function):
        values: Input[list[float]]
        result: Output[float]

        @runtime
        def run(self) -> None:
            self.result = abs(self.values)

    with pytest.raises(IRValidationError, match="operator_type"):
        ListMagnitude().to_ir()


def test_numeric_calls_require_one_positional_argument():
    class Precision(Function):
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = round(2.5, 0)

    class Keyword(Function):
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = round(number=2.5)

    class NoArgument(Function):
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = abs()

    for instance in (Precision(), Keyword(), NoArgument()):
        with pytest.raises(IRValidationError, match="one positional argument"):
            instance.to_ir()
