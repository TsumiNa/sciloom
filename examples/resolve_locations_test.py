"""Author, direct IR and JSON queries use the same fixed location semantics."""

from pathlib import Path

import pytest

from examples.developer.zone_ir import build_program, example_directory
from examples.resolve_locations import ResolveLocations
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import Zone
from sciloom_autosuite import AutoSuiteTarget


@pytest.mark.parametrize(
    "first,second,identities",
    [
        ("first rack", "second rack", ("well:27", "well:0", "well:8")),
        ("second rack", "first rack", ("well:0", "well:8", "well:27")),
        ("absent", "first rack", ("well:27", "well:0")),
        ("absent", "absent", ()),
        ("first rack", "first rack", ("well:27", "well:0")),
    ],
)
def test_all_entry_routes(first, second, identities):
    for program in (ResolveLocations().to_ir(), build_program()):
        before = to_json(program)
        for candidate in (program, from_json(before)):
            outputs = (
                Interpreter(candidate, environment=ReferenceEnvironment(locations=example_directory()))
                .run(inputs={"first_name": first, "second_name": second})
                .outputs
            )
            assert outputs == {"selected": Zone(well_ids=identities), "count": len(identities)}
        assert to_json(program) == before


def test_companions_are_current():
    assert (
        ResolveLocations().compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("resolve_locations.asfp").read_bytes()
    )
    assert to_json(build_program()) == Path(__file__).with_name("developer").joinpath("zone_ir.json").read_text(
        encoding="utf-8"
    )
