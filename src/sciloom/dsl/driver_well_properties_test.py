"""Well metadata stays ordered, typed and independent of device configuration."""

import pytest

from sciloom import Function, Input, Output, Var, WellProperty, Zone, log, runtime
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, WellProperties, WellPropertyReadEvent
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import LocationDirectory, Well


class Label(Function):
    selection: Input[Zone]
    label: Input[str]
    well: Var[Zone] = Zone.empty()
    previous: Output[str]

    def __init__(self):
        self.sample_label = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        self.sample_label[self.selection] = self.label
        self.label = "later"
        self.previous = "no wells"
        for self.well in self.selection:
            self.previous = self.sample_label.get(self.well, default="missing")


class ReadLabel(Function):
    selection: Input[Zone]
    result: Var[str] = "unchanged"

    def __init__(self):
        self.label = WellProperty("sample_ID", str)

    @runtime
    def run(self) -> None:
        log("before", category="test", stream="order")
        self.result = self.label.get(self.selection)
        log("after", category="test", stream="order")


class ReadDefault(ReadLabel):
    @runtime
    def run(self) -> None:
        self.result = self.label.get(self.selection, default="fallback")


def environment(store=None):
    return ReferenceEnvironment(
        locations=LocationDirectory(wells=(Well(identity="a", name="A"), Well(identity="b", name="B"))),
        properties=WellProperties() if store is None else store,
    )


def test_capture_identity_snapshots_roundtrip_and_explicit_sharing():
    original = Label().to_ir()
    for program in (original, from_json(to_json(original))):
        env = environment()
        session = Interpreter(program, environment=env)
        result = session.run(inputs={"selection": Zone(well_ids=("b", "a")), "label": "試料 <A> 'quoted'"})
        assert result.outputs == {"previous": "試料 <A> 'quoted'"}
        assert [e.zone.well_ids for e in result.events] == [("b", "a"), ("b",), ("a",)]
        assert all(e.value == "試料 <A> 'quoted'" for e in result.events)
        assert all(not e.used_default for e in result.events if isinstance(e, WellPropertyReadEvent))
        old = env.properties.snapshot()
        session.run(inputs={"selection": Zone(well_ids=("a",)), "label": "new"})
        assert old[("a", "sample_ID")] == "試料 <A> 'quoted'"
        shared = Interpreter(ReadLabel().to_ir(), environment=env)
        assert shared.run(inputs={"selection": Zone(well_ids=("a",))}).state["fn:0"]["fn:0:var:result"] == "new"
        assert not environment().properties.snapshot()
        assert len(result.events) == 3
        assert session.run(inputs={"selection": Zone.empty(), "label": "unused"}).outputs == {"previous": "no wells"}
        assert len(env.properties.snapshot()) == 2
    assert Label().to_ir() == original


def test_strict_failure_preserves_destination_and_prior_effects():
    env = environment()
    session = Interpreter(ReadLabel().to_ir(), environment=env)
    with pytest.raises(ExecutionError, match="well_property_missing"):
        session.run(inputs={"selection": Zone(well_ids=("a",))})
    assert [e.value for e in env.events] == ["before"]
    assert session._state["fn:0"]["fn:0:var:result"] == "unchanged"


@pytest.mark.parametrize("kind", ["missing", "wrong_type", "bad_return"])
def test_default_recovers_only_missing_or_incompatible_property(kind):
    class ExternalProperties(WellProperties):
        def get(self, well_id, name):
            if kind == "missing":
                raise KeyError(name)
            if kind == "wrong_type":
                raise TypeError("stored integer")
            return 7

    env = environment(ExternalProperties())
    result = Interpreter(ReadDefault().to_ir(), environment=env).run(inputs={"selection": Zone(well_ids=("a",))})
    assert result.state["fn:0"]["fn:0:var:result"] == "fallback"
    assert result.events[0].used_default
    with pytest.raises(ExecutionError, match="well_property_missing|well_property_type"):
        Interpreter(ReadLabel().to_ir(), environment=env).run(inputs={"selection": Zone(well_ids=("a",))})


@pytest.mark.parametrize(
    "selection,code",
    [
        (Zone.empty(), "well_property_selection"),
        (Zone(well_ids=("a", "b")), "well_property_selection"),
        (Zone(well_ids=("unknown",)), "unknown_well"),
    ],
)
def test_default_does_not_recover_bad_selection(selection, code):
    env = environment()
    with pytest.raises(ExecutionError, match=code):
        Interpreter(ReadDefault().to_ir(), environment=env).run(inputs={"selection": selection})
    assert not env.events


def test_invalid_write_validates_all_wells_before_mutation():
    env = environment()
    with pytest.raises(ExecutionError, match="unknown_well"):
        Interpreter(Label().to_ir(), environment=env).run(
            inputs={"selection": Zone(well_ids=("a", "unknown")), "label": "bad"}
        )
    assert not env.properties.snapshot()
    assert not env.events
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(Label().to_ir()).run(inputs={"selection": Zone.empty(), "label": "empty"})


def test_provider_failures_are_not_defaults_or_transactions():
    class Broken(WellProperties):
        def get(self, well_id, name):
            raise OSError("offline")

        def set(self, well_ids, name, value):
            super().set(well_ids[:1], name, value)
            raise OSError("partial write")

    env = environment(Broken())
    empty = Interpreter(Label().to_ir(), environment=env).run(inputs={"selection": Zone.empty(), "label": "unused"})
    assert empty.outputs == {"previous": "no wells"}
    assert len(empty.events) == 1 and empty.events[0].zone == Zone.empty()
    with pytest.raises(ExecutionError, match="property_service_error"):
        Interpreter(ReadDefault().to_ir(), environment=env).run(inputs={"selection": Zone(well_ids=("a",))})
    with pytest.raises(ExecutionError, match="property_service_error"):
        Interpreter(Label().to_ir(), environment=env).run(
            inputs={"selection": Zone(well_ids=("a", "b")), "label": "partial"}
        )
    assert env.properties.snapshot() == {("a", "sample_ID"): "partial"}
    assert env.events == empty.events


def test_default_is_eager_even_if_property_exists():
    class Eager(ReadLabel):
        values: Input[list[str]]

        @runtime
        def run(self) -> None:
            self.result = self.label.get(self.selection, default=self.values[0])

    env = environment(WellProperties({("a", "sample_ID"): "present"}))
    with pytest.raises(ExecutionError, match="index_bounds"):
        Interpreter(Eager().to_ir(), environment=env).run(inputs={"selection": Zone(well_ids=("a",)), "values": []})
    assert not env.events


def test_host_guards_and_schema_types():
    for name, value_type in [("", str), (3, str), ("x", int)]:
        with pytest.raises((TypeError, ValueError)):
            WellProperty(name, value_type)
    prop = WellProperty("x", str)
    with pytest.raises(TypeError, match="@runtime"):
        prop.get(Zone.empty())
    with pytest.raises(TypeError, match="@runtime"):
        prop[Zone.empty()] = "a"

    class Wrong(Label):
        @runtime
        def run(self) -> None:
            self.sample_label[self.selection] = 3

    with pytest.raises(IRValidationError, match="well_property_type"):
        Wrong().to_ir()


def test_nested_get_and_augmented_write_are_rejected():
    class Nested(ReadLabel):
        @runtime
        def run(self) -> None:
            self.result = self.label.get(self.selection) + "suffix"

    class Augmented(ReadLabel):
        @runtime
        def run(self) -> None:
            self.label[self.selection] += "suffix"

    for model, code in [(Nested, "external_operation"), (Augmented, "well_property_write")]:
        with pytest.raises(IRValidationError, match=code):
            model().to_ir()


def test_properties_are_shared_across_function_calls_by_well_identity():
    class Write(Function):
        location: Input[Zone]

        def __init__(self):
            self.label = WellProperty("sample_ID", str)

        @runtime
        def run(self) -> None:
            self.label[self.location] = "from child"

    class Parent(ReadLabel):
        def __init__(self):
            super().__init__()
            self.write = Write()

        @runtime
        def run(self) -> None:
            self.write(location=self.selection)
            self.result = self.label.get(self.selection)

    result = Interpreter(Parent().to_ir(), environment=environment()).run(inputs={"selection": Zone(well_ids=("b",))})
    assert result.state["fn:0"]["fn:0:var:result"] == "from child"
    assert [e.value for e in result.events] == ["from child", "from child"]


def test_write_rhs_is_evaluated_before_zone_selection():
    class Capture(Function):
        rack: Input[Zone]
        values: Input[list[str]]

        def __init__(self):
            self.label = WellProperty("sample_ID", str)

        @runtime
        def run(self) -> None:
            self.label[self.rack[0]] = self.values[1]

    program = Capture().to_ir()
    with pytest.raises(ExecutionError) as captured:
        Interpreter(program, environment=environment()).run(inputs={"rack": Zone.empty(), "values": []})
    assert captured.value.diagnostics[0].node_id == program.functions[0].body[0].value.node_id
