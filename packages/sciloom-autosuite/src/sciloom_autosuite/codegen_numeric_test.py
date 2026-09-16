"""Documented math expression mappings; the wire evaluator is not an Executor."""

import math
import xml.etree.ElementTree as ET

import pytest

from sciloom import Duration, Function, Input, Output, Volume, mL, runtime, s
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .target import AutoSuiteTarget


class Magnitudes(Function):
    value: Input[float]
    values: Input[list[float]]
    amount: Input[Volume]
    interval: Input[Duration]
    count: Input[int]
    absolute: Output[float]
    first: Output[float]
    whole: Output[int]
    volume: Output[Volume]
    duration: Output[Duration]
    rounded_count: Output[int]
    floored_count: Output[int]

    @runtime
    def run(self) -> None:
        self.absolute = abs(self.value)
        self.first = abs(self.values[0])
        self.whole = math.floor(self.value)
        self.volume = abs(self.amount)
        self.duration = abs(self.interval)
        self.rounded_count = round(self.count)
        self.floored_count = math.floor(self.count)


@pytest.mark.parametrize("value", [-3.5, -1.2, -0.5, 0.0, 2.5, 3.5])
def test_native_abs_floor_and_integer_identity(value):
    authored = Magnitudes().to_ir()
    for program in (authored, from_json(to_json(authored))):
        content = compile_ir(program, target=AutoSuiteTarget()).artifact.content
        wire = WireModel(content).run({"value": value, "values": [-4.0], "amount": -2e-6, "interval": -3.0, "count": 3})
        expected = (
            Interpreter(program)
            .run(
                inputs={
                    "value": value,
                    "values": [-4.0],
                    "amount": -2 * mL,
                    "interval": -3 * s,
                    "count": 3,
                }
            )
            .outputs
        )
        assert wire == {**expected, "volume": expected["volume"].m3, "duration": expected["duration"].seconds}
        expressions = ET.fromstring(content).findall(".//expressiontext")
        assert any(e.text == "floor(value)" for e in expressions)
        assert any(e.text == "abs(value)" for e in expressions)
        assert not any("round(" in (e.text or "") for e in expressions)
        # A checked array operand is materialized once before abs reads it.
        assert sum("[" in (e.text or "") for e in expressions) == 1


def test_unproven_real_rounding_is_rejected_with_source_diagnostic():
    class Rounded(Function):
        value: Input[float]
        result: Output[int]

        @runtime
        def run(self) -> None:
            self.result = round(self.value)

    with pytest.raises(CompilationError) as error:
        Rounded().compile(target=AutoSuiteTarget())
    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == "unsupported_rounding"
    assert "ties-to-even" in diagnostic.message
    assert diagnostic.source is not None
    # Reference execution remains available, including large finite values.
    assert Interpreter(Rounded().to_ir()).run(inputs={"value": 1e100}).outputs["result"] == round(1e100)


@pytest.mark.requires_corpus
def test_abs_floor_expression_spellings_have_latest_app_evidence():
    root = ET.parse(corpus_file("extracted/latest_app/functions/30_Dynamic Transfer Volumectrically.asfp"))
    expressions = [e.text or "" for e in root.iter() if e.tag in {"expressiontext", "conditionif"}]
    assert "floor(current_idx / max_chunk_size) * max_chunk_size + max_chunk_size - 1" in expressions
    assert any("abs(current_residual_vol - ch1_start_vol)" in e for e in expressions)
