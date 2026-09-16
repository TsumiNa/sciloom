"""The documented calculation and generated companion match the actual example."""

from pathlib import Path

import pytest

from examples.numeric_operations import CalculatePortions
from sciloom import mL
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteTarget


def test_numeric_calculation_and_companion():
    instance = CalculatePortions()
    result = Interpreter(instance.to_ir()).run(inputs={"amount": 2.5 * mL, "reference": 3 * mL})
    assert result.outputs["whole_portions"] == 2
    assert result.outputs["difference"].m3 == pytest.approx(0.5e-6)
    assert (
        instance.compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("numeric_operations.asfp").read_bytes()
    )
