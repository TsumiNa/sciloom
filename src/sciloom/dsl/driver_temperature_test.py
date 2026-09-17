"""Thermal fields retain affine semantics through source, JSON and calls."""

import pytest

from sciloom import (
    Function,
    Input,
    Output,
    Temperature,
    TemperatureDifference,
    TemperatureRate,
    Var,
    csv,
    degC,
    degC_per_min,
    delta_degC,
    kelvin_per_s,
    log,
    runtime,
)
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, LogEvent, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json


class RaiseTemperature(Function):
    initial: Input[Temperature]
    delta: Input[TemperatureDifference]
    target: Output[Temperature]
    calls: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.target = self.initial + self.delta
        self.calls += 1
        log(self.target, category="thermal", stream="adjusted")


class ThermalValues(Function):
    supplied: Input[Temperature]
    rates: Input[list[TemperatureRate]]
    target: Output[Temperature]
    difference: Output[TemperatureDifference]
    rate: Output[TemperatureRate]
    positive: Output[bool]
    copied: Output[list[TemperatureRate]]
    temperatures: Output[list[Temperature]]
    differences: Output[list[TemperatureDifference]]
    c_per_min: Output[float]
    saved: Var[Temperature] = -20 * degC
    offsets: Var[list[TemperatureDifference]] = [5 * delta_degC]

    def __init__(self) -> None:
        self.adjust = RaiseTemperature()

    @runtime
    def run(self) -> None:
        self.target = self.adjust(initial=self.supplied, delta=self.offsets[0])
        self.difference = self.target - self.saved
        self.positive = self.target > self.saved
        self.rate = 2 * self.rates[0] + 1 * kelvin_per_s
        self.c_per_min = self.rate / degC_per_min
        self.copied = self.rates
        self.copied[0] *= 2
        self.temperatures = [self.saved, self.target]
        self.temperatures[0] += 1 * delta_degC
        self.differences = self.offsets
        self.offsets[0] += 1 * delta_degC
        self.saved = self.target
        log(self.target, category="thermal", stream="target")


def test_thermal_fields_lists_calls_snapshots_and_json():
    program = ThermalValues().to_ir()
    assert program.format_version == 4
    restored = from_json(to_json(program))
    assert restored == program
    for candidate in (program, restored):
        session = Interpreter(candidate)
        inputs = {"supplied": 20 * degC, "rates": [60 * degC_per_min]}
        result = session.run(inputs=inputs)
        assert result.outputs["target"] == 25 * degC
        assert result.outputs["difference"] == 45 * delta_degC
        assert result.outputs["positive"] is True
        assert result.outputs["rate"] == 3 * kelvin_per_s
        assert result.outputs["c_per_min"] == pytest.approx(180)
        assert result.outputs["copied"] == (2 * kelvin_per_s,)
        assert result.outputs["temperatures"] == (-19 * degC, 25 * degC)
        assert result.outputs["differences"] == (5 * delta_degC,)
        assert inputs["rates"] == [1 * kelvin_per_s]
        event = result.events[-1]
        assert isinstance(event, LogEvent) and event.value == 25 * degC
        second = session.run(inputs=inputs)
        assert second.outputs["target"] == 26 * degC
        assert second.outputs["difference"] == 1 * delta_degC
        assert result.outputs["target"] == 25 * degC
        assert result.outputs["differences"] == (5 * delta_degC,)


def test_absolute_zero_failure_precedes_later_log():
    program = RaiseTemperature().to_ir()
    for candidate in (program, from_json(to_json(program))):
        environment = ReferenceEnvironment()
        session = Interpreter(candidate, environment=environment)
        with pytest.raises(ExecutionError, match="invalid_temperature"):
            session.run(inputs={"initial": Temperature(kelvin=0), "delta": -1 * delta_degC})
        assert environment.events == ()
        # Fatal arithmetic cannot update the following persistent counter.
        result = session.run(inputs={"initial": 0 * degC, "delta": 1 * delta_degC})
        assert result.outputs["target"] == 1 * degC
        counter = next(v for v in candidate.functions[0].variables if v.name == "calls")
        assert result.state[counter.owner_id][counter.node_id] == 1


@pytest.mark.parametrize("value", [1.0, True, 1 * delta_degC, 1 * kelvin_per_s])
def test_typed_input_rejects_wrong_dimension(value):
    with pytest.raises(ExecutionError, match="runtime_type"):
        Interpreter(RaiseTemperature().to_ir()).run(inputs={"initial": value, "delta": 1 * delta_degC})


def test_invalid_thermal_defaults_and_csv_host_descriptor():
    with pytest.raises(IRValidationError, match="class_schema"):

        class BadDefault(Function):
            value: Var[Temperature] = 1 * delta_degC

    for kind in (Temperature, TemperatureDifference, TemperatureRate):
        with pytest.raises(ValueError, match="Thermal CSV"):
            csv.Column(index=0, value_type=kind)


def test_runtime_absolute_unit_is_not_an_implicit_cast():
    class BadCast(Function):
        number: Input[float]
        result: Output[Temperature]

        @runtime
        def run(self) -> None:
            self.result = self.number * degC

    with pytest.raises(IRValidationError, match="operator_type"):
        BadCast().to_ir()


def test_source_thermal_csv_read_explicitly_rejects():
    class ThermalCsv(Function):
        value: Output[Temperature]

        @runtime
        def run(self) -> None:
            (self.value,) = csv.read_row(
                "thermal.csv", row=0, header=False, columns=(csv.Column(index=0, value_type=Temperature),)
            )

    with pytest.raises(IRValidationError, match="unsupported_csv_type"):
        ThermalCsv().to_ir()


def test_thermal_csv_append_preserves_canonical_bytes_and_typed_events():
    class ThermalAppend(Function):
        @runtime
        def run(self) -> None:
            csv.append_row("thermal.csv", values=(20 * degC, -2 * delta_degC, 60 * degC_per_min))

    program = ThermalAppend().to_ir()
    for candidate in (program, from_json(to_json(program))):
        files = MemoryFiles()
        session = Interpreter(candidate, environment=ReferenceEnvironment(files=files))
        result = session.run()
        assert files.read_bytes("thermal.csv") == b"293.15,-2.0,1.0\r\n"
        assert result.events[-1].values == (20 * degC, -2 * delta_degC, 1 * kelvin_per_s)
