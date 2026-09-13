"""Composition discovery reaches every composed Function under a usable name."""

import pytest

from sciloom import Agitator, Function, Output, rpm, runtime


class Stage(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm
        self.agitator.start()


class Workflow(Function):
    agitator: Agitator

    def __init__(self):
        self.stage = Stage()

    @runtime
    def run(self):
        self.stage()
        self.agitator.stop()


def test_distinct_slots_have_stable_component_paths():
    program = Workflow().to_ir()
    assert [resource.logical_id for resource in program.resources] == ["agitator", "stage.agitator"]


def test_composition_under_a_private_name_is_rejected():
    class Step(Function):
        result: Output[int]

        @runtime
        def run(self):
            self.result = 1

    class Hidden(Function):
        result: Output[int]

        def __init__(self):
            self._step = Step()

        @runtime
        def run(self):
            self.result = 2

    with pytest.raises(TypeError, match="public Python identifiers"):
        Hidden().to_ir()
