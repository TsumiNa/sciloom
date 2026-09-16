"""Compiled author example and Python/direct-IR/JSON grouped traversal agree."""

from pathlib import Path

import pytest

from examples.developer.zone_traversal_ir import build_program
from examples.visit_locations import VisitLocations
from sciloom import Function, Input, Output, Var, Zone, runtime, zones
from sciloom.core.diagnostics import ExecutionError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteTarget


class VisitPairs(Function):
    rack: Input[Zone]
    first: Output[Zone]
    groups: Output[int]
    last: Output[Zone]
    fragment: Var[Zone] = Zone.empty()

    @runtime
    def run(self) -> None:
        self.first = Zone.empty()
        self.groups = 0
        if len(self.rack) > 0:
            self.first = self.rack[0]
        for self.fragment in zones.fragments(self.rack, size=2):
            self.groups += 1
        self.last = self.fragment


@pytest.mark.parametrize("identities", [(), ("well:27", "well:0"), ("well:27", "well:0", "well:8", "well:2")])
def test_grouped_python_direct_and_json_routes(identities):
    for program in (VisitPairs().to_ir(), build_program()):
        before = to_json(program)
        for candidate in (program, from_json(before)):
            result = Interpreter(candidate).run(inputs={"rack": Zone(well_ids=identities)})
            assert result.outputs == {
                "first": Zone(well_ids=identities[:1]),
                "groups": len(identities) // 2,
                "last": Zone(well_ids=identities[-2:]),
            }
            with pytest.raises(ExecutionError, match="zone_fragment_size"):
                Interpreter(candidate).run(inputs={"rack": Zone(well_ids=("one",))})
        assert to_json(program) == before


def test_author_visit_resets_count_preserves_last_and_keeps_sessions_independent():
    program = VisitLocations().to_ir()
    session = Interpreter(program)
    first = session.run(inputs={"rack": Zone(well_ids=("27", "0", "8"))})
    assert first.outputs == {"count": 3, "last": Zone(well_ids=("8",))}
    assert session.run(inputs={"rack": Zone.empty()}).outputs == {"count": 0, "last": Zone(well_ids=("8",))}
    assert Interpreter(program).run(inputs={"rack": Zone.empty()}).outputs == {"count": 0, "last": Zone.empty()}
    assert first.outputs["count"] == 3


def test_companions_are_current():
    assert (
        VisitLocations().compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("visit_locations.asfp").read_bytes()
    )
    assert to_json(build_program()) == Path(__file__).with_name("developer").joinpath(
        "zone_traversal_ir.json"
    ).read_text(encoding="utf-8")
