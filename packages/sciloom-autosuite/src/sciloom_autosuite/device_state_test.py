"""Private configuration transport preserves shared device state across calls."""

import xml.etree.ElementTree as ET

import pytest

from sciloom import Agitator, Function, Input, rpm, runtime
from sciloom.core.ir import to_json
from . import AutoSuiteIndividualShaker, AutoSuiteTarget

SET = "Chemspeed.SATaskSetVariable.1"
CALL = "Chemspeed.SATaskExecuteFunction.1"
STIR = "Chemspeed.SATaskSetAgitation.1"


class Configure(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm


class Start(Function):
    agitator: Agitator

    @runtime
    def run(self):
        self.agitator.start()


class ParentConfigure(Function):
    agitator: Agitator

    def __init__(self):
        self.child = Start()
        self.child.agitator = self.agitator

    @runtime
    def run(self):
        self.agitator.speed = 600 * rpm
        self.child()


class ChildConfigure(Function):
    agitator: Agitator

    def __init__(self):
        self.child = Configure()
        self.child.agitator = self.agitator

    @runtime
    def run(self):
        self.child()
        self.agitator.start()


def target():
    return AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})


@pytest.mark.parametrize("cls", [ParentConfigure, ChildConfigure])
def test_entry_storage_and_private_callee_parameters_match(cls):
    model = cls()
    authored = model.to_ir()
    result = model.compile(target=target())
    root = ET.fromstring(result.artifact.content)
    entry, callee = list(root)
    assert result.semantic_ir == authored
    assert "sciloom_device" not in to_json(result.semantic_ir)
    assert entry.findtext("functiondata/inputs/count") == "0"
    assert entry.findtext("functiondata/outputs/count") == "0"
    assert len(entry.findall(".//variable")) == 1
    storage = entry.findtext(".//variable/name")
    incoming = callee.find("functiondata/inputs/item0")
    outgoing = callee.find("functiondata/outputs/item0")
    call = entry.find(f".//*[@typeid='{CALL}']")
    assert call.findtext("functiondata/inputs/item0/expression") == storage
    assert call.findtext("functiondata/outputs/item0/variablename") == storage
    assert call.findtext("functiondata/inputs/item0/id") == incoming.findtext("id")
    assert call.findtext("functiondata/outputs/item0/id") == outgoing.findtext("id")
    first_write = callee.find(f".//*[@typeid='{SET}']")
    assert first_write.findtext("variablename") == outgoing.findtext("variablename")
    assert first_write.findtext("expressiontext") == incoming.findtext("variablename")
    stir = root.find(f".//*[@typeid='{STIR}']")
    expected = outgoing.findtext("variablename") if cls is ParentConfigure else storage
    assert stir.findtext("taskdatas/taskdata0/speed") == expected
    assert stir.findtext("switchon") == "1"


def test_conditional_callee_returns_incoming_configuration_on_unchanged_branch():
    class MaybeConfigure(Function):
        agitator: Agitator
        change: Input[bool]

        @runtime
        def run(self):
            if self.change:
                self.agitator.speed = 300 * rpm

    class Parent(Function):
        agitator: Agitator

        def __init__(self):
            self.child = MaybeConfigure()
            self.child.agitator = self.agitator

        @runtime
        def run(self):
            self.agitator.speed = 600 * rpm
            self.child(change=False)
            self.agitator.start()

    root = ET.fromstring(Parent().compile(target=target()).artifact.content)
    callee = list(root)[1]
    assert callee.findtext("functiondata/inputs/count") == "2"
    assert callee.findtext("functiondata/outputs/count") == "1"
    # The copy precedes the conditional Macro, so either branch produces output.
    components = list(callee.find("components"))
    assert components[0].get("typeid") == SET
    assert components[0].findtext("expressiontext") == callee.findtext("functiondata/inputs/item1/variablename")
    assert components[0].findtext("variablename") == callee.findtext("functiondata/outputs/item0/variablename")
