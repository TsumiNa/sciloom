"""Device declarations remain distinct from variables and share by reference."""

import pytest

from sciloom import Agitator, Function, Input, Var, rpm, runtime
from sciloom.contrib.autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.devices import BaseDevice


class Stage(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm
        self.agitator.start()


class Workflow(Function):
    agitator: Agitator
    count: int = 3

    def __init__(self, *, share=True):
        self.stage = Stage()
        if share:
            self.stage.agitator = self.agitator

    @runtime
    def run(self):
        self.stage()
        self.agitator.stop()


def test_annotation_slots_share_identity_and_state_without_runtime_variables():
    model = Workflow()
    assert model.model_fields == {}
    assert model.agitator is model.stage.agitator
    assert model.agitator is not Workflow().agitator
    program = model.to_ir()
    assert program == model.to_ir()
    assert program.format_version == 4
    assert [resource.logical_id for resource in program.resources] == ["agitator"]
    result = Interpreter(program).run()
    assert len(result.resources) == 1
    assert result.resources["resource:agitator"].applied_configuration["speed"] == 600 * rpm
    assert not result.resources["resource:agitator"].enabled
    target = AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})
    assert model.compile(target=target).artifact.content.startswith(b"<?xml")


def test_distinct_slots_have_stable_component_paths():
    program = Workflow(share=False).to_ir()
    assert [resource.logical_id for resource in program.resources] == ["agitator", "stage.agitator"]


def test_inherited_and_class_composed_devices_keep_declarations():
    class Inherited(Stage):
        pass

    class Composed(Function):
        stage = Inherited()

        @runtime
        def run(self):
            self.stage()

    assert tuple(Inherited.device_fields) == ("agitator",)
    assert Composed().to_ir().resources[0].logical_id == "stage.agitator"


def test_slot_rejects_hardware_plain_values_and_host_operations():
    stage = Stage()
    for value in (42, Agitator(), BaseDevice(), AutoSuiteIndividualShaker(zone="A", device_id="23")):
        with pytest.raises(TypeError, match="logical device reference"):
            stage.agitator = value
    with pytest.raises(TypeError, match="compiled"):
        stage.agitator.stop()
    other = Stage()
    stage.agitator = other.agitator
    with pytest.raises(IRValidationError, match="device_reference"):
        stage.to_ir()


def test_invalid_declarations_and_inherited_role_changes():
    with pytest.raises(TypeError, match="class-level"):
        class Default(Function):
            agitator: Agitator = Agitator()

    with pytest.raises(TypeError, match="change type"):
        class HostOverride(Stage):
            agitator: int

    with pytest.raises(TypeError, match="change type"):
        class VariableOverride(Stage):
            agitator: Var[int] = 0

    with pytest.raises(TypeError, match="shadowed"):
        class Shadow(Stage):
            agitator = "host"

    with pytest.raises(TypeError, match="Invalid"):
        class Reserved(Function):
            compile: Agitator

    class Generic(Function):
        device: BaseDevice
    assert tuple(Generic.device_fields) == ("device",)

    with pytest.raises(IRValidationError, match="class_schema"):
        class Wrapped(Function):
            agitator: Input[Agitator]


def test_unused_declared_slot_still_requires_a_binding():
    class Empty(Function):
        agitator: Agitator

        @runtime
        def run(self):
            pass

    assert Empty().to_ir().resources[0].logical_id == "agitator"


def test_lowering_does_not_write_references_into_user_instances():
    model = Workflow(share=False)
    before = vars(model).copy(), vars(model.stage).copy()
    model.to_ir()
    assert (vars(model), vars(model.stage)) == before
    reference = model.agitator
    assert reference is model.agitator
    assert vars(model) == before[0]


def test_reference_cache_does_not_leak_functions_or_require_hashability():
    import gc
    import weakref

    class Unhashable(Stage):
        __hash__ = None

    model = Unhashable()
    reference = model.agitator
    assert reference is model.agitator
    model.to_ir()
    weak = weakref.ref(model)
    del reference, model
    gc.collect()
    assert weak() is None


@pytest.mark.parametrize("kind", ["value", "annotation", "property"])
def test_devices_cannot_replace_inherited_host_members(kind):
    namespace = {"__annotations__": {"stage": int}} if kind == "annotation" else {
        "stage": property(lambda self: 1) if kind == "property" else 1,
    }
    host = type("Host", (Function,), namespace)
    with pytest.raises(TypeError, match="inherited host"):
        type("Child", (host,), {"__annotations__": {"stage": Agitator}})
