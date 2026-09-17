"""Transfer quantities survive fields, calls, lists, JSON and reference services."""

import pytest

from examples.developer.transfer_values_ir import build_program
from examples.transfer_settings import TransferSettings
from sciloom import FlowRate, Function, Input, Length, Output, Var, csv, log, m3_per_s, metre, mL_per_min, mm, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from sciloom.core.specialization import specialize


class ScaleFlow(Function):
    value: Input[FlowRate]
    result: Output[FlowRate]

    @runtime
    def run(self) -> None:
        self.result = self.value * 2


class Values(Function):
    flows: Input[list[FlowRate]]
    length: Input[Length]
    flow: Output[FlowRate]
    lengths: Output[list[Length]]
    copied: Output[list[FlowRate]]
    count: Output[float]
    shorter: Output[bool]
    saved: Var[Length] = 2 * mm
    history: Var[list[FlowRate]] = [0 * mL_per_min]

    def __init__(self):
        self.scale = ScaleFlow()

    @runtime
    def run(self) -> None:
        self.flow = self.scale(value=self.flows[0])
        self.count = self.flow / mL_per_min
        self.shorter = self.length < self.saved
        self.lengths = [self.saved, self.length]
        self.lengths[0] += 1 * mm
        self.copied = self.flows
        self.copied[0] *= 2
        self.saved = self.length
        self.history[0] += self.flow
        log(self.flow, category="transfer", stream="flow")


def test_source_direct_ir_json_and_specialization_match():
    direct = build_program()
    for program in (
        direct,
        TransferSettings().to_ir(),
        from_json(to_json(direct)),
        specialize(direct, bindings=DeviceBindings()),
    ):
        assert program.format_version == 4
        result = Interpreter(program).run(inputs={"factor": 60.0})
        assert result.outputs["flow"].m3_per_second == pytest.approx(1e-6)
        assert result.outputs["clearance"] == 2 * mm
        assert from_json(to_json(program)) == program


def test_lists_calls_captured_values_and_persistent_state():
    source = Values().to_ir()
    for program in (source, from_json(to_json(source))):
        session = Interpreter(program)
        supplied = [3 * mL_per_min]
        result = session.run(inputs={"flows": supplied, "length": 1 * mm})
        assert result.outputs["flow"] == 6 * mL_per_min
        assert result.outputs["count"] == pytest.approx(6)
        assert result.outputs["shorter"] is True
        assert result.outputs["lengths"] == (3 * mm, 1 * mm)
        assert result.outputs["copied"] == (6 * mL_per_min,)
        assert supplied == [3 * mL_per_min]
        assert result.events[-1].value == 6 * mL_per_min
        second = session.run(inputs={"flows": supplied, "length": 1 * mm})
        assert second.outputs["shorter"] is False
        assert second.outputs["lengths"] == (2 * mm, 1 * mm)
        assert result.outputs["lengths"] == (3 * mm, 1 * mm)
        saved = next(v for v in program.functions[0].variables if v.name == "history")
        assert second.state[saved.owner_id][saved.node_id] == pytest.approx(((12 * mL_per_min).m3_per_second,))


@pytest.mark.parametrize("bad", [1.0, True, 1 * mm])
def test_flow_inputs_reject_untyped_or_wrong_dimension(bad):
    with pytest.raises(ExecutionError, match="runtime_type"):
        Interpreter(ScaleFlow().to_ir()).run(inputs={"value": bad})


def test_invalid_default_and_cross_dimension_source():
    with pytest.raises(IRValidationError, match="class_schema"):

        class BadDefault(Function):
            flow: Var[FlowRate] = 1 * mm

    class BadExpression(Function):
        result: Output[FlowRate]

        @runtime
        def run(self):
            self.result = 1 * mL_per_min + 1 * mm

    with pytest.raises(IRValidationError, match="operator_type"):
        BadExpression().to_ir()


def test_numeric_failure_has_no_following_log():
    class Overflow(Function):
        value: Input[FlowRate]
        doubled: Output[FlowRate]

        @runtime
        def run(self):
            self.doubled = self.value * 2
            log(self.doubled, category="transfer", stream="overflow")

    program = Overflow().to_ir()
    env = ReferenceEnvironment()
    with pytest.raises(ExecutionError, match="numeric_error"):
        Interpreter(program, environment=env).run(inputs={"value": 1e308 * m3_per_s})
    assert env.events == ()


class CsvValues(Function):
    flow: Output[FlowRate]
    length: Output[Length]

    @runtime
    def run(self):
        self.flow, self.length = csv.read_row(
            "settings.csv",
            row=0,
            header=False,
            columns=(
                csv.Column(index=0, value_type=FlowRate, unit=mL_per_min),
                csv.Column(index=1, value_type=Length, unit=mm),
            ),
        )
        csv.append_row("canonical.csv", values=(self.flow, self.length))


def test_explicit_csv_units_read_and_append_canonical_values():
    for program in (CsvValues().to_ir(), from_json(to_json(CsvValues().to_ir()))):
        files = MemoryFiles({"settings.csv": b"60,-2\r\n"})
        result = Interpreter(program, environment=ReferenceEnvironment(files=files)).run()
        assert result.outputs["flow"] == 1e-6 * m3_per_s
        assert result.outputs["length"] == -0.002 * metre
        assert files.read_bytes("canonical.csv") == b"1e-06,-0.002\r\n"
    for kind, unit in ((FlowRate, mL_per_min), (Length, mm)):
        assert csv.Column(index=0, value_type=kind, unit=unit).unit is unit
        with pytest.raises(ValueError, match="explicit matching unit"):
            csv.Column(index=0, value_type=kind)
    with pytest.raises(ValueError, match="does not match"):
        csv.Column(index=0, value_type=FlowRate, unit=mm)
