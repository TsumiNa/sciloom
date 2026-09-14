"""Production agitation payloads constrain the backend, not the semantic model."""

import xml.etree.ElementTree as ET
from dataclasses import replace

import pytest

from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Var, rpm, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import ConfigureProperty, from_json, to_json
from . import AutoSuiteIndividualShaker, AutoSuiteTarget
from .conftest import corpus_file

AGITATION = "Chemspeed.SATaskSetAgitation.1"


class ConfigureAgitation(Function):
    shaker_speed: Input[RotationalSpeed]
    enabled: Input[bool]

    agitator: Agitator

    @runtime
    def run(self):
        if self.enabled:
            self.agitator.speed = self.shaker_speed
            self.agitator.start()
        else:
            self.agitator.stop()


def target(zone="Heater Shaker 23", device_id="23"):
    return AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone=zone, device_id=device_id)})


def shape(element):
    """Ignore only tag context, timestamps and UUID spelling at the task boundary."""

    def visit(node):
        text = (node.text or "").strip()
        if node.tag in ("id", "edittime"):
            text = node.tag
        return node.tag, node.attrib, text, tuple(visit(child) for child in node)

    return element.attrib, tuple(visit(child) for child in element)


def test_production_task_payload_and_typed_input_relationship():
    source = ET.parse(corpus_file("extracted/latest_app/functions/24_Sample and Run GPC.asfp"))
    reference = sorted(
        source.findall(f".//*[@typeid='{AGITATION}']"), key=lambda t: t.findtext("switchon"), reverse=True
    )
    assert [task.findtext("switchon") for task in reference] == ["1", "0"]
    result = ConfigureAgitation().compile(target=target())
    root = ET.fromstring(result.artifact.content)
    generated = root.findall(f".//*[@typeid='{AGITATION}']")
    assert len(generated) == 2
    # Production uses a runtime Zone parameter. This deployment binds it to a
    # concrete zone and its individual shaker; these are the only payload changes.
    for task in reference:
        task.find("zone").text = "Heater Shaker 23"
        task.find("taskdatas/taskdata0/progid").text = "Chemspeed.SADeviceIndividualShaker.1"
        task.find("taskdatas/taskdata0/deviceid").text = "23"
    reference[0].find("taskdatas/taskdata0/speed").text = generated[0].findtext("taskdatas/taskdata0/speed")
    assert [shape(task) for task in generated] == [shape(task) for task in reference]
    speed = root.find("function/functiondata/inputs/item0")
    vendor_speed = source.find(".//functiondata/inputs/item0")
    assert speed.findtext("variabletype") == vendor_speed.findtext("variabletype") == "angularspeed"
    saved_name = generated[0].findtext("taskdatas/taskdata0/speed")
    capture = root.find(".//*[@typeid='Chemspeed.SATaskSetVariable.1']")
    assert capture.findtext("variablename") == saved_name
    assert capture.findtext("expressiontext") == speed.findtext("variablename")
    assert len(result.semantic_ir.functions[0].variables) == 2


def test_concrete_zone_address_and_canonical_speed_match_standalone_export():
    class Start(Function):
        agitator: Agitator

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            self.agitator.start()

    root = ET.fromstring(Start().compile(target=target("1st_vial", "24")).artifact.content)
    generated = root.find(f".//*[@typeid='{AGITATION}']")
    reference = next(
        task
        for task in ET.parse(corpus_file("asfp/functionsPackage_3.asfp")).getroot().iter()
        if task.get("typeid") == AGITATION and task.findtext("zone") == "1st_vial" and task.findtext("switchon") == "1"
    )
    assert reference.findtext("taskdatas/taskdata0/speed") == "10"
    capture = root.find(".//*[@typeid='Chemspeed.SATaskSetVariable.1']")
    assert capture.findtext("expressiontext") == "10"
    assert capture.findtext("variablename") == generated.findtext("taskdatas/taskdata0/speed")
    reference.find("taskdatas/taskdata0/speed").text = generated.findtext("taskdatas/taskdata0/speed")
    assert shape(generated) == shape(reference)


def test_rebinding_changes_only_target_representation():
    program = ConfigureAgitation().to_ir()
    snapshot = to_json(program)
    first = compile_ir(program, target=target())
    second = compile_ir(program, target=target("Heater Shaker 25", "25"))
    assert to_json(program) == snapshot
    assert first.semantic_ir == second.semantic_ir == program
    assert first.artifact != second.artifact
    assert compile_ir(from_json(snapshot), target=target()).artifact == first.artifact
    assert isinstance(program.functions[0].body[0].then_body[0], ConfigureProperty)
    assert not any(word in snapshot for word in ("Chemspeed", "Heater Shaker", "device_id"))
    for result, zone, device_id in ((first, "Heater Shaker 23", "23"), (second, "Heater Shaker 25", "25")):
        task = ET.fromstring(result.artifact.content).find(f".//*[@typeid='{AGITATION}']")
        assert task.findtext("zone") == zone
        assert task.findtext("taskdatas/taskdata0/deviceid") == device_id
    session = Interpreter(program)
    for speed in (300 * rpm, 1200 * rpm):
        assert (
            session.run(inputs={"shaker_speed": speed, "enabled": True}).events[-1].state.applied_configuration["speed"]
            == speed
        )
    assert first.artifact == compile_ir(program, target=target()).artifact


def test_quantities_keep_units_in_locals_outputs_and_call_bindings():
    class Echo(Function):
        speed: Input[RotationalSpeed]
        result: Output[RotationalSpeed]

        @runtime
        def run(self):
            self.result = self.speed

    class Caller(Function):
        speed: Var[RotationalSpeed] = 600 * rpm
        result: Output[RotationalSpeed]

        agitator: Agitator

        def __init__(self):
            self.echo = Echo()

        @runtime
        def run(self):
            self.result = self.echo(speed=self.speed)
            self.agitator.speed = self.result
            self.agitator.start()

    result = Caller().compile(target=target())
    root = ET.fromstring(result.artifact.content)
    local = root.find(".//variable")
    assert [local.findtext(path) for path in ("value/type", "value/value", "siunit", "unit")] == [
        "5",
        "10",
        "1/s",
        "rpm",
    ]
    assert {n.text for n in root.iter("variabletype")} == {"angularspeed"}
    echo = next(f for f in root if f.findtext("name") == "Echo")
    call = root.find(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']")
    for group in ("inputs", "outputs"):
        assert call.findtext(f"functiondata/{group}/item0/id") == echo.findtext(f"functiondata/{group}/item0/id")
    assert Interpreter(result.semantic_ir).run().outputs == {"result": 600 * rpm}


def test_agitation_composes_with_loops_and_independent_resources():
    class Sequence(Function):
        index: Var[int] = 0

        def __init__(self):
            self.first = ConfigureAgitation()
            self.second = ConfigureAgitation()

        @runtime
        def run(self):
            while self.index < 2:
                self.first(shaker_speed=600 * rpm, enabled=True)
                self.index += 1
            self.second(shaker_speed=300 * rpm, enabled=False)

    config = replace(
        target(),
        devices={
            "first.agitator": target().devices["agitator"],
            "second.agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 25", device_id="25"),
        },
    )
    result = Sequence().compile(target=config)
    reordered = replace(config, devices=dict(reversed(tuple(config.devices.items()))))
    assert Sequence().compile(target=reordered).artifact == result.artifact
    tasks = ET.fromstring(result.artifact.content).findall(f".//*[@typeid='{AGITATION}']")
    assert len(tasks) == 4
    assert {t.findtext("zone") for t in tasks} == {"Heater Shaker 23", "Heater Shaker 25"}
    events = Interpreter(result.semantic_ir).run().events
    assert [(e.resource_id, e.state.enabled) for e in events] == [
        ("resource:first.agitator", False),
        ("resource:first.agitator", True),
        ("resource:first.agitator", True),
        ("resource:first.agitator", True),
        ("resource:second.agitator", False),
    ]
    assert events[-1].state.applied_configuration == {}


def test_stop_has_no_speed_dependency_or_hidden_runtime_state():
    class Stop(Function):
        agitator: Agitator

        @runtime
        def run(self):
            self.agitator.stop()

    result = Stop().compile(target=target())
    root = ET.fromstring(result.artifact.content)
    assert root.find(".//variable") is None
    assert root.findtext("function/functiondata/inputs/count") == "0"
    task = root.find(f".//*[@typeid='{AGITATION}']")
    assert task.findtext("switchon") == "0"
    assert Interpreter(result.semantic_ir).run().events[0].state.applied_configuration == {}


def test_missing_or_unknown_target_bindings_fail_before_emission(monkeypatch):
    def fail(*args):
        pytest.fail("emission must not run with invalid bindings")

    monkeypatch.setattr(AutoSuiteTarget, "emit", fail)
    with pytest.raises(CompilationError, match="missing_resource_binding"):
        ConfigureAgitation().compile(target=AutoSuiteTarget())
    config = AutoSuiteTarget(devices={"typo": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})
    with pytest.raises(CompilationError, match="unknown_resource_binding"):
        ConfigureAgitation().compile(target=config)


def test_example_binding_matches_latest_application_configuration():
    app = ET.parse(corpus_file("extracted/latest_app/application.xml"))
    zone = next(z for z in app.iter("zone") if z.findtext("name") == "Heater Shaker 23")
    well = zone.find("well")
    shaker = next(
        e
        for e in app.iter("element")
        if e.get("typeid") == "Chemspeed.SADeviceIndividualShaker.1" and e.findtext("deviceid") == "23"
    )
    assert any(
        e.get("typeid") == well.get("progID") and e.findtext("deviceid") == well.get("deviceID")
        for e in shaker.iter("element")
    )
