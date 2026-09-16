"""Quantity encoding compares corpus fields and a modeled SI expression evaluator."""

import gzip
import xml.etree.ElementTree as ET

import pytest

from sciloom import Duration, Function, Input, Output, RotationalSpeed, Var, Volume, minute, mL, rpm, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import ScalarType
from .codegen_arrays_test import WireModel
from .conftest import corpus_file
from .encoding import SCALARS
from .target import AutoSuiteTarget


class QuantityValues(Function):
    amount: Input[Volume]
    elapsed: Input[Duration]
    number: Input[float]
    volume: Output[Volume]
    duration: Output[Duration]
    magnitude: Output[float]
    samples: Output[list[Volume]]
    initial_volume: Var[Volume] = 1 * mL
    initial_time: Var[Duration] = 1 * minute

    @runtime
    def run(self) -> None:
        self.volume = self.amount + self.number * mL
        self.duration = self.initial_time - self.elapsed
        self.magnitude = self.volume / mL
        self.samples = [self.volume, self.initial_volume]


def test_quantity_parameters_initials_and_si_expressions():
    content = QuantityValues().compile(target=AutoSuiteTarget()).artifact.content
    root = ET.fromstring(content)
    assert root.findtext(".//functiondata/inputs/item0/variabletype") == "volume"
    assert root.findtext(".//functiondata/inputs/item1/variabletype") == "time"
    declarations = {v.findtext("name"): v for v in root.findall(".//variable")}
    assert declarations["initial_volume"].findtext("siunit") == "m^3"
    assert float(declarations["initial_volume"].findtext("value/value")) == 1e-6
    assert declarations["initial_time"].findtext("siunit") == "s"
    assert float(declarations["initial_time"].findtext("value/value")) == 60
    result = WireModel(content).run({"amount": 1e-6, "elapsed": 90.0, "number": 2.0})
    assert result["volume"] == pytest.approx(3e-6)
    assert result["duration"] == -30.0
    assert result["magnitude"] == pytest.approx(3.0)
    assert result["samples"] == pytest.approx([3e-6, 1e-6])


@pytest.mark.requires_corpus
def test_duration_parameter_keyword_has_app_evidence():
    path = corpus_file("app/config20260820.app")
    root = ET.fromstring(gzip.decompress(path.read_bytes()))
    function = next(f for f in root.iter("function") if f.findtext("name") == "GPC Analysis Prep and No Delay")
    assert function.findtext("functiondata/inputs/item0/name") == "analysis_time"
    assert function.findtext("functiondata/inputs/item0/variabletype") == SCALARS[ScalarType.DURATION].parameter_type


@pytest.mark.requires_corpus
@pytest.mark.parametrize(
    "file,kind,name,expected",
    [
        ("31_Get Aspirate Chunk.asfp", ScalarType.VOLUME, "fp_eplison_vol", 1e-12),
        ("13_Run GPC Analysis.asfp", ScalarType.DURATION, "next_prep_time", 294.0),
    ],
)
def test_quantity_initials_use_canonical_units(file, kind, name, expected):
    root = ET.parse(corpus_file("extracted/latest_app/functions/" + file))
    variable = next(v for v in root.findall(".//variable") if v.findtext("name") == name)
    assert variable.findtext("value/type") == SCALARS[kind].storage_type
    assert variable.findtext("siunit") == SCALARS[kind].si_unit
    assert float(variable.findtext("value/value")) == expected


def test_unverified_runtime_quantity_checks_are_refused():
    class Ratio(Function):
        a: Input[Volume]
        b: Input[Volume]
        result: Output[float]

        @runtime
        def run(self) -> None:
            self.result = self.a / self.b

    class Speed(Function):
        number: Input[float]
        result: Output[RotationalSpeed]

        @runtime
        def run(self) -> None:
            self.result = self.number * rpm

    class Indexed(Function):
        values: Input[list[Duration]]
        result: Output[Duration]

        @runtime
        def run(self) -> None:
            self.result = self.values[0]

    for function in (Ratio(), Speed(), Indexed()):
        with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
            function.compile(target=AutoSuiteTarget())


def test_signed_quantity_literal_divisor_needs_no_runtime_guard():
    class NegativeRatio(Function):
        amount: Input[Volume]
        result: Output[float]

        @runtime
        def run(self) -> None:
            self.result = self.amount / (-1 * mL)

    content = NegativeRatio().compile(target=AutoSuiteTarget()).artifact.content
    assert WireModel(content).run({"amount": 2e-6}) == {"result": -2.0}


def test_speed_scaling_with_a_proven_factor_compiles():
    class ScaleSpeed(Function):
        speed: Input[RotationalSpeed]
        result: Output[RotationalSpeed]

        @runtime
        def run(self) -> None:
            self.result = self.speed * 2

    content = ScaleSpeed().compile(target=AutoSuiteTarget()).artifact.content
    assert WireModel(content).run({"speed": 10.0}) == {"result": 20.0}
