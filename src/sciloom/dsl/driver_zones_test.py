"""Zone fields, calls and lookup failures retain value and session boundaries."""

from types import SimpleNamespace

import pytest

from sciloom import Function, Input, Output, Var, Zone, runtime, zones
from sciloom.core.diagnostics import ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import LocationDirectory, Well


class Echo(Function):
    selection: Input[Zone]
    result: Output[Zone]

    @runtime
    def run(self) -> None:
        self.result = self.selection
        self.selection = Zone.empty()


class Accumulate(Function):
    incoming: Input[Zone]
    saved: Var[Zone] = Zone.empty()
    result: Output[Zone]

    def __init__(self):
        self.echo = Echo()

    @runtime
    def run(self) -> None:
        self.saved = zones.combine(self.saved, self.incoming)
        self.result = self.echo(selection=self.saved)


def test_zone_calls_snapshots_and_persistent_state_are_isolated():
    for candidate in (Accumulate().to_ir(), from_json(to_json(Accumulate().to_ir()))):
        session = Interpreter(candidate)
        first = session.run(inputs={"incoming": Zone(well_ids=("well:27",))})
        second = session.run(inputs={"incoming": Zone(well_ids=("well:0",))})
        assert first.outputs["result"].well_ids == ("well:27",)
        assert second.outputs["result"].well_ids == ("well:27", "well:0")
        assert Interpreter(candidate).run(inputs={"incoming": Zone.empty()}).outputs["result"] == Zone.empty()


class Name(Function):
    selection: Input[Zone]
    label: Output[str]

    @runtime
    def run(self) -> None:
        self.label = zones.well_name(self.selection)


def test_well_label_requires_one_known_identity_and_a_directory():
    directory = LocationDirectory(wells=(Well(identity="physical:27", name="Rack: Well #27"),))
    for candidate in (Name().to_ir(), from_json(to_json(Name().to_ir()))):
        session = Interpreter(candidate, environment=ReferenceEnvironment(locations=directory))
        assert session.run(inputs={"selection": Zone(well_ids=("physical:27",))}).outputs == {"label": "Rack: Well #27"}
        for identities, code in (
            ((), "zone_cardinality"),
            (("physical:27", "other"), "zone_cardinality"),
            (("other",), "unknown_well"),
        ):
            with pytest.raises(ExecutionError, match=code):
                session.run(inputs={"selection": Zone(well_ids=identities)})
        with pytest.raises(ExecutionError, match="missing_environment_service"):
            Interpreter(candidate).run(inputs={"selection": Zone(well_ids=("physical:27",))})


def test_lookup_never_uses_an_implicit_directory():
    class Find(Function):
        selected: Output[Zone]

        @runtime
        def run(self) -> None:
            self.selected = zones.find("unknown")

    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(Find().to_ir()).run()
    assert (
        Interpreter(Find().to_ir(), environment=ReferenceEnvironment(locations=LocationDirectory()))
        .run()
        .outputs["selected"]
        == Zone.empty()
    )


@pytest.mark.parametrize("value", [0, True, (), [], "well:27"])
def test_zone_input_rejects_raw_ids_and_other_containers(value):
    with pytest.raises(ExecutionError, match="runtime_type"):
        Interpreter(Echo().to_ir()).run(inputs={"selection": value})


def test_declaration_defaults_inheritance_and_host_guard():
    class Base(Function):
        selected: Var[Zone] = Zone.empty()

    class Child(Base):
        pass

    assert Child.model_fields == Base.model_fields
    instance = Child()
    with pytest.raises(IRValidationError, match="runtime_field_read"):
        _ = instance.selected
    with pytest.raises(IRValidationError, match="runtime_field_write"):
        instance.selected = Zone.empty()
    with pytest.raises(IRValidationError, match="class_schema"):

        class Missing(Function):
            selected: Var[Zone]

    with pytest.raises(IRValidationError, match="class_schema"):

        class IntegerDefault(Function):
            selected: Var[Zone] = 0

    with pytest.raises(IRValidationError, match="class_schema"):

        class Nested(Function):
            selected: Var[list[Zone]] = []


def test_zone_language_restrictions():
    class Truth(Function):
        selected: Input[Zone]

        @runtime
        def run(self) -> None:
            if self.selected:
                self.selected = Zone.empty()

    class Add(Function):
        selected: Input[Zone]
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            self.result = self.selected + self.selected

    class Equal(Function):
        selected: Input[Zone]
        result: Output[bool]

        @runtime
        def run(self) -> None:
            self.result = self.selected == self.selected

    class Slice(Function):
        selected: Input[Zone]
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            self.result = self.selected[:]

    for cls, code in (
        (Truth, "condition_type"),
        (Add, "operator_type"),
        (Equal, "operator_type"),
        (Slice, "python_subset"),
    ):
        with pytest.raises(IRValidationError, match=code):
            cls().to_ir()


def test_marker_aliases_and_host_guards():
    find = zones.find

    class Aliased(Function):
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            self.result = find(name="absent")

    assert (
        Interpreter(Aliased().to_ir(), environment=ReferenceEnvironment(locations=LocationDirectory()))
        .run()
        .outputs["result"]
        == Zone.empty()
    )
    for marker, args in (
        (zones.find, ("a",)),
        (zones.combine, (Zone.empty(), Zone.empty())),
        (zones.well_name, (Zone.empty(),)),
    ):
        with pytest.raises(TypeError, match="@runtime"):
            marker(*args)

    def forbidden(*args, **kwargs):
        raise AssertionError("Host implementation must not execute.")

    fake = SimpleNamespace(find=forbidden)

    class Fake(Function):
        result: Output[Zone]

        @runtime
        def run(self) -> None:
            self.result = fake.find("a")

    with pytest.raises(IRValidationError, match="python_subset"):
        Fake().to_ir()
