"""Capacity arithmetic, resume behavior and retained vendor formula evidence."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from examples.aspiration_chunk import AspirationChunk
from examples.developer.source_paths import repository_relative
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom.units import mL
from sciloom_autosuite import AutoSuiteTarget


def inputs(**changes):
    return {
        "volumes": [1 * mL, 2 * mL, 4 * mL],
        "start_idx": 0,
        "start_residual": 0 * mL,
        "max_idx": 2,
        "syringe": 5 * mL,
        "airgap": 0.5 * mL,
        "safety": 0.25 * mL,
        "extra": 0.25 * mL,
        **changes,
    }


def test_partial_fill_resume_and_reset_after_json_restoration():
    for program in (AspirationChunk().to_ir(), from_json(to_json(repository_relative(AspirationChunk().to_ir())))):
        session = Interpreter(program)
        first = session.run(inputs=inputs())
        assert first.outputs["valid"]
        assert first.outputs["next_idx"] == 2 and first.outputs["end_idx"] == 2
        assert first.outputs["end_dispense"] / mL == pytest.approx(1)
        assert first.outputs["next_residual"] / mL == pytest.approx(3)
        assert first.outputs["aspirate"] / mL == pytest.approx(4.25)
        resumed = session.run(inputs=inputs(start_idx=2, start_residual=first.outputs["next_residual"]))
        assert resumed.outputs["next_idx"] == 3
        assert resumed.outputs["next_residual"] == 0 * mL
        assert resumed.outputs["aspirate"] / mL == pytest.approx(3.25)
        assert session.run(inputs=inputs()).outputs == first.outputs
        assert first.outputs["next_idx"] == 2


@pytest.mark.parametrize(
    "changes, next_idx, end_idx, aspirate, residual",
    [
        ({"volumes": []}, 0, -1, 0, 0),
        ({"volumes": [0 * mL, 0 * mL]}, 2, 1, 0, 0),
        ({"start_idx": 3}, 3, 2, 0, 0),
        ({"volumes": [4 * mL]}, 1, 0, 4.25, 0),
        ({"volumes": [(4 + 0.0000005) * mL]}, 1, 0, 4.25, 0),
        ({"volumes": [0.5 * mL] * 6, "start_idx": 3, "max_idx": 5}, 4, 3, 0.75, 0),
        ({"max_idx": 0}, 1, 0, 1.25, 0),
        ({"start_residual": 0.5 * mL, "max_idx": 0}, 1, 0, 0.75, 0),
        ({"volumes": [1 * mL], "start_residual": 1.0000005 * mL}, 1, 0, 1.2500005, 0),
    ],
)
def test_empty_zero_exact_tolerance_and_aligned_boundary(changes, next_idx, end_idx, aspirate, residual):
    output = Interpreter(AspirationChunk().to_ir()).run(inputs=inputs(**changes)).outputs
    assert output["valid"]
    assert (output["next_idx"], output["end_idx"]) == (next_idx, end_idx)
    assert output["aspirate"] / mL == pytest.approx(aspirate)
    assert output["next_residual"] / mL == pytest.approx(residual)


@pytest.mark.parametrize(
    "changes",
    [
        {"start_idx": -1},
        {"start_idx": 4},
        {"start_idx": 3, "start_residual": 1 * mL},
        {"start_residual": -1 * mL},
        {"max_idx": -1},
        {"syringe": 1 * mL},
        {"airgap": 0 * mL},
        {"safety": 0 * mL},
        {"extra": -1 * mL},
        {"volumes": [1 * mL, -1 * mL], "max_idx": 0},
        {"volumes": [1 * mL], "start_residual": 2 * mL},
        {"volumes": [0 * mL], "start_residual": 0.01 * mL},
        {"start_idx": 2, "start_residual": 4.000002 * mL},
    ],
)
def test_invalid_input_has_defined_outputs_without_partial_packing(changes):
    program = AspirationChunk().to_ir()
    for entry in (program, from_json(to_json(program))):
        output = Interpreter(entry).run(inputs=inputs(**changes)).outputs
        assert not output["valid"]
        assert output["aspirate"] == output["end_dispense"] == output["next_residual"] == 0 * mL
        assert output["next_idx"] == changes.get("start_idx", 0)


def test_host_configuration_companion_and_native_boundary():
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="positive host integer"):
            AspirationChunk(chunk_size=invalid)
    with pytest.raises(CompilationError, match="unsupported_runtime_guard"):
        AspirationChunk().compile(target=AutoSuiteTarget())
    text = to_json(repository_relative(AspirationChunk().to_ir()))
    assert Path(__file__).parent.joinpath("developer/aspiration_chunk_ir.json").read_text() == text
    assert str(Path(__file__).resolve().parents[1]) not in text


@pytest.mark.requires_corpus
def test_original_capacity_and_boundary_formulas_remain_read_only_evidence():
    corpus = Path(__file__).resolve().parents[1] / "autosuite/corpus/extracted/latest_app/functions"
    paths = sorted(corpus.glob("3[01]_*.asfp"))
    if len(paths) != 2:
        pytest.skip("Local F30/F31 evidence is absent.")
    before = {path: path.read_bytes() for path in paths}
    values = {
        path.name[:2]: {e.text.strip() for e in ET.fromstring(data).iter() if e.text and e.text.strip()}
        for path, data in before.items()
    }
    assert "floor(current_idx / max_chunk_size) * max_chunk_size + max_chunk_size - 1" in values["30"]
    assert "syringe_vol - airgap_vol - extra_vol - safe_vol" in values["31"]
    assert all(path.read_bytes() == data for path, data in before.items())
