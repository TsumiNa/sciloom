"""The author/direct-IR paths agree and checked-in companions are current."""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, WellProperties
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom_autosuite import AutoSuiteTarget
from .developer.well_properties_ir import build_program
from .label_wells import LabelWells


def test_source_direct_ir_json_agree_on_values_and_stored_labels():
    directory = LocationDirectory(wells=(Well(identity="a", name="A"), Well(identity="b", name="B")))
    for program in (LabelWells().to_ir(), build_program(), from_json(to_json(build_program()))):
        env = ReferenceEnvironment(locations=directory, properties=WellProperties())
        session = Interpreter(program, environment=env)
        for ids in ((), ("a",), ("b", "a")):
            result = session.run(inputs={"rack": Zone(well_ids=ids), "label": "batch"})
            assert result.outputs == {"last_label": "batch" if ids else ""}
            assert [e.zone.well_ids for e in result.events] == [ids, *((identity,) for identity in ids)]
        assert env.properties.snapshot() == {("a", "sample_ID"): "batch", ("b", "sample_ID"): "batch"}


def test_property_companions_match_generating_programs():
    root = Path(__file__).parent
    assert (root / "label_wells.asfp").read_bytes() == LabelWells().compile(target=AutoSuiteTarget()).artifact.content
    assert (root / "developer/well_properties_ir.json").read_text() == to_json(build_program())
