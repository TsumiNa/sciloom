"""Production agitation payloads constrain the backend, not the semantic model."""

import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

from sciloom import Agitator, Boolean, Function, Input, Integer, Output, RotationalSpeed, compile_ir, rpm, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import SetAgitation, from_json, to_json
from . import AutoSuiteTarget, IndividualShakerBinding

CORPUS = Path(__file__).resolve().parents[4] / "autosuite"
AGITATION = "Chemspeed.SATaskSetAgitation.1"


class ConfigureAgitation(Function):
    shaker_speed: Input[RotationalSpeed]
    enabled: Input[Boolean]

    def __init__(self, name="reaction_mixer"):
        self.agitator = Agitator(name)

    @runtime
    def run(self):
        if self.enabled:
            self.agitator.set_speed(self.shaker_speed)
        else:
            self.agitator.stop()


def target(zone="Heater Shaker 23", device_id="23"):
    return AutoSuiteTarget(
        agitators=(IndividualShakerBinding(logical_id="reaction_mixer", zone=zone, device_id=device_id),)
    )


def shape(element):
    """Ignore only tag context, timestamps and UUID spelling at the task boundary."""

    def visit(node):
        text = (node.text or "").strip()
        if node.tag in ("id", "edittime"):
            text = node.tag
        return node.tag, node.attrib, text, tuple(visit(child) for child in node)

    return element.attrib, tuple(visit(child) for child in element)


def test_production_task_payload_and_typed_input_relationship():
    source = ET.parse(CORPUS / "extracted/latest_app/functions/24_Sample and Run GPC.asfp")
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
    assert [shape(task) for task in generated] == [shape(task) for task in reference]
    speed = root.find("function/functiondata/inputs/item0")
    vendor_speed = source.find(".//functiondata/inputs/item0")
    assert speed.findtext("variabletype") == vendor_speed.findtext("variabletype") == "angularspeed"
    assert generated[0].findtext("taskdatas/taskdata0/speed") == speed.findtext("variablename")
    assert all(task.tag == "component" for task in generated)


def test_concrete_zone_address_and_canonical_speed_match_standalone_export():
    class Start(Function):
        def __init__(self):
            self.agitator = Agitator("reaction_mixer")

        @runtime
        def run(self):
            self.agitator.set_speed(600 * rpm)

    root = ET.fromstring(Start().compile(target=target("1st_vial", "24")).artifact.content)
    generated = root.find(f".//*[@typeid='{AGITATION}']")
    reference = next(
        task
        for task in ET.parse(CORPUS / "asfp/functionsPackage_3.asfp").getroot().iter()
        if task.get("typeid") == AGITATION and task.findtext("zone") == "1st_vial" and task.findtext("switchon") == "1"
    )
    assert shape(generated) == shape(reference)
    assert generated.findtext("taskdatas/taskdata0/speed") == "10"


def test_rebinding_changes_only_target_representation():
    program = ConfigureAgitation().to_ir()
    snapshot = to_json(program)
    first = compile_ir(program, target=target())
    second = compile_ir(program, target=target("Heater Shaker 25", "25"))
    assert to_json(program) == snapshot
    assert first.semantic_ir == second.semantic_ir == program
    assert first.artifact != second.artifact
    assert compile_ir(from_json(snapshot), target=target()).artifact == first.artifact
    assert isinstance(program.functions[0].body[0].then_body[0], SetAgitation)
    assert not any(word in snapshot for word in ("Chemspeed", "Heater Shaker", "device_id"))
    for result, zone, device_id in ((first, "Heater Shaker 23", "23"), (second, "Heater Shaker 25", "25")):
        task = ET.fromstring(result.artifact.content).find(f".//*[@typeid='{AGITATION}']")
        assert task.findtext("zone") == zone
        assert task.findtext("taskdatas/taskdata0/deviceid") == device_id
    session = Interpreter(program)
    for speed in (300 * rpm, 1200 * rpm):
        assert session.run(inputs={"shaker_speed": speed, "enabled": True}).events[0].speed == speed
    assert first.artifact == compile_ir(program, target=target()).artifact


def test_quantities_keep_units_in_locals_outputs_and_call_bindings():
    class Echo(Function):
        speed: Input[RotationalSpeed]
        result: Output[RotationalSpeed]

        @runtime
        def run(self):
            self.result = self.speed

    class Caller(Function):
        speed: RotationalSpeed = 600 * rpm
        result: Output[RotationalSpeed]

        def __init__(self):
            self.echo = Echo()
            self.agitator = Agitator("reaction_mixer")

        @runtime
        def run(self):
            self.result = self.echo(speed=self.speed)
            self.agitator.set_speed(self.result)

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
        index: Integer = 0

        def __init__(self):
            self.first = ConfigureAgitation()
            self.second = ConfigureAgitation("other_mixer")

        @runtime
        def run(self):
            while self.index < 2:
                self.first(shaker_speed=600 * rpm, enabled=True)
                self.index += 1
            self.second(shaker_speed=300 * rpm, enabled=False)

    config = replace(
        target(),
        agitators=(
            *target().agitators,
            IndividualShakerBinding(logical_id="other_mixer", zone="Heater Shaker 25", device_id="25"),
        ),
    )
    result = Sequence().compile(target=config)
    reordered = replace(config, agitators=tuple(reversed(config.agitators)))
    assert Sequence().compile(target=reordered).artifact == result.artifact
    tasks = ET.fromstring(result.artifact.content).findall(f".//*[@typeid='{AGITATION}']")
    assert len(tasks) == 4
    assert {t.findtext("zone") for t in tasks} == {"Heater Shaker 23", "Heater Shaker 25"}
    events = Interpreter(result.semantic_ir).run().events
    assert [(e.resource_id, e.enabled) for e in events] == [
        ("resource:reaction_mixer", True),
        ("resource:reaction_mixer", True),
        ("resource:other_mixer", False),
    ]
    assert events[-1].speed is None


def test_stop_has_no_speed_dependency_or_hidden_runtime_state():
    class Stop(Function):
        def __init__(self):
            self.agitator = Agitator("reaction_mixer")

        @runtime
        def run(self):
            self.agitator.stop()

    result = Stop().compile(target=target())
    root = ET.fromstring(result.artifact.content)
    assert root.find(".//variable") is None
    assert root.findtext("function/functiondata/inputs/count") == "0"
    task = root.find(f".//*[@typeid='{AGITATION}']")
    assert task.findtext("switchon") == "0"
    assert Interpreter(result.semantic_ir).run().events[0].speed is None


def test_missing_or_unknown_target_bindings_fail_before_emission(monkeypatch):
    def fail(*args):
        pytest.fail("emission must not run with invalid bindings")

    monkeypatch.setattr(AutoSuiteTarget, "emit", fail)
    with pytest.raises(CompilationError, match="missing_resource_binding"):
        ConfigureAgitation().compile(target=AutoSuiteTarget())
    config = AutoSuiteTarget(
        agitators=(IndividualShakerBinding(logical_id="typo", zone="Heater Shaker 23", device_id="23"),)
    )
    with pytest.raises(CompilationError, match="unknown_resource_binding"):
        ConfigureAgitation().compile(target=config)


def test_example_binding_matches_latest_application_configuration():
    app = ET.parse(CORPUS / "extracted/latest_app/application.xml")
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
