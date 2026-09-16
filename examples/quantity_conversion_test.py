"""Verify the author's quantity example and its same-name artifact."""

from pathlib import Path

import pytest

from examples.quantity_conversion import QuantityConversion
from sciloom import mL, s
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteTarget


def test_quantity_conversion():
    function = QuantityConversion()
    result = Interpreter(function.to_ir()).run(inputs={"amount": 1 * mL, "extra_ml": 2.0, "elapsed": 90 * s})
    assert result.outputs["total"].m3 == pytest.approx(3e-6)
    assert result.outputs["total_ml"] == pytest.approx(3.0)
    assert result.outputs["difference"] == -30 * s
    assert (
        function.compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("quantity_conversion.asfp").read_bytes()
    )
