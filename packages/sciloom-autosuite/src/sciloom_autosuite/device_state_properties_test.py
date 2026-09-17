"""Synthetic property transport uses existing wire primitives, not a native profile.

The internal emission harness and WireModel exercise copy/parameter scheduling.
They are deliberately not public target adapters or Executor acceptance evidence.
"""

from dataclasses import FrozenInstanceError
from uuid import NAMESPACE_URL

import pytest

from examples.developer.lifecycle_commands import AdjustableAgitator
from sciloom import Function, Input, Var, rpm, runtime
from sciloom.core.diagnostics import CompilationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import ListType, ScalarType, from_json, to_json
from sciloom.devices import operation
from .agitation import AutoSuiteIndividualShaker
from .codegen_arrays_test import WireModel
from .context import CodegenContext
from .device_state import prepare_device_state
from .functions import build_functions
from .target import AutoSuiteTarget
from .xml import AutoSuiteVersion


class ArrayDevice(AdjustableAgitator):
    device_type_id = "test.config-array/v1"

    @property
    def curve(self) -> list[int]:
        raise TypeError("Configuration is write-only.")

    @curve.setter
    @operation(id="test.config-array.curve/v1")
    def curve(self, value: list[int]) -> None: ...


class Capture(Function):
    device: ArrayDevice
    values: Input[list[int]]
    gain: Input[float]
    change: Input[bool]

    @runtime
    def run(self):
        if self.change:
            self.device.curve = self.values
            self.device.gain = self.gain
            self.device.speed = 300 * rpm
            self.values[0] = 99
            self.gain = 9.0


class Middle(Function):
    device: ArrayDevice
    values: Input[list[int]]
    change: Input[bool]

    def __init__(self):
        self.child = Capture()
        self.child.device = self.device

    @runtime
    def run(self):
        self.child(values=self.values, gain=2.0, change=self.change)
        self.values[0] = 77


class CaptureAcrossCalls(Function):
    device: ArrayDevice
    values: Var[list[int]] = [2, 4]
    change: Input[bool]

    def __init__(self):
        self.middle = Middle()
        self.middle.device = self.device
        self.middle.child.device = self.device
        self.independent = Capture()

    @runtime
    def run(self):
        self.values = [2, 4]
        self.device.curve = [1, 2]
        self.device.gain = 1.0
        self.device.speed = 600 * rpm
        self.independent(values=[5], gain=5.0, change=True)
        self.middle(values=self.values, change=self.change)
        self.values[0] = 88


@pytest.mark.parametrize("change", [False, True])
def test_typed_properties_capture_values_through_nested_calls_without_aliasing(change):
    program = from_json(to_json(CaptureAcrossCalls().to_ir()))
    before = to_json(program)
    context = CodegenContext(program, NAMESPACE_URL, {})
    prepare_device_state(context)
    entry = program.entry_function_id
    storage = context.device_state[entry]
    assert len(storage) == 6  # Three properties on each of two distinct resources.
    assert {value.type for value in storage.values()} == {
        ScalarType.ROTATIONAL_SPEED,
        ScalarType.REAL,
        ListType(element_type=ScalarType.INTEGER),
    }
    assert len({value.name for value in storage.values()}) == 6
    with pytest.raises(FrozenInstanceError):
        next(iter(storage.values())).name = "overwritten"
    serialization = build_functions(context, AutoSuiteVersion.V2_47_1_1)
    assert to_json(program) == before
    assert "sciloom_device_" not in before and "sciloom_tmp_" not in before
    machine = WireModel(serialization.to_xml())
    reference = Interpreter(program)
    properties = {p.semantic_id: p.name for contract in program.device_types for p in contract.properties}
    for _ in range(2):
        machine.run({"change": change})
        result = reference.run(inputs={"change": change})
        saved = machine.state[context.identifier("locals", entry)]
        for (resource, property_id), value in storage.items():
            expected = result.resources[resource].configuration[properties[property_id]]
            if value.type == ScalarType.ROTATIONAL_SPEED:
                expected = 5.0 if change or "independent" in resource else 10.0
            elif isinstance(value.type, ListType):
                expected = list(expected)
            assert saved[value.name] == expected
        assert result.resources["resource:device"].configuration["curve"] == ((2, 4) if change else (1, 2))
        assert result.resources["resource:independent.device"].configuration["curve"] == (5,)
        assert all(not state.enabled and state.applied_configuration == {} for state in result.resources.values())

    # Each call passes every property it transitively uses, with matching scalar
    # units/array flags and parameter IDs. List transport uses distinct buffers.
    for call in machine.root.findall(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']"):
        callee = machine.functions[call.findtext("functionid")]
        for group in ("inputs", "outputs"):
            expected = {
                item.findtext("id"): item
                for item in callee.findall(f"functiondata/{group}/*")
                if item.tag.startswith("item")
            }
            for actual in call.findall(f"functiondata/{group}/*"):
                if actual.tag.startswith("item"):
                    declared = expected[actual.findtext("id")]
                    assert actual.findtext("variabletype") == declared.findtext("variabletype")
                    assert actual.findtext("isarray") == declared.findtext("isarray")
        incoming_arrays = {
            item.findtext("variablename")
            for item in call.findall("functiondata/inputs/*")
            if item.findtext("isarray") == "1"
        }
        outgoing_arrays = {
            item.findtext("variablename")
            for item in call.findall("functiondata/outputs/*")
            if item.findtext("isarray") == "1"
        }
        assert incoming_arrays.isdisjoint(outgoing_arrays)


def test_synthetic_storage_does_not_grant_an_autosuite_profile():
    with pytest.raises(CompilationError, match="device_type"):
        CaptureAcrossCalls().compile(
            target=AutoSuiteTarget(
                devices={
                    "device": AutoSuiteIndividualShaker(zone="bench", device_id="23"),
                    "independent.device": AutoSuiteIndividualShaker(zone="other", device_id="25"),
                }
            )
        )
