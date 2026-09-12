"""Validate deployment identities before delegating code generation."""

from dataclasses import replace

import pytest

from .compiler import compile_ir
from .compiler_test import TextTarget, program
from .devices import DeviceBinding, DeviceBindings, validate_bindings
from .diagnostics import CompilationError
from .ir import DeviceResource
from .ir.device_contracts import AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT, AGITATOR_TYPE_ID, AGITATION_SPEED_ID, START_AGITATION_ID, STOP_AGITATION_ID


def binding():
    return DeviceBinding(logical_id="mixer", contract=AGITATOR_CONTRACT, base_contracts=(BASE_DEVICE_CONTRACT,), writable_properties=(AGITATION_SPEED_ID,), supported_operations=(START_AGITATION_ID, STOP_AGITATION_ID), physical_id="test:1")


def test_resolver_cannot_silently_drop_or_mistype_dependencies():
    source = replace(program(), resources=(DeviceResource(node_id="r", logical_id="mixer", device_type_id=AGITATOR_TYPE_ID),), device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT))
    target = TextTarget()
    with pytest.raises(CompilationError, match="missing_resource_binding"):
        compile_ir(source, target=target)
    assert not target.emitted
    assert validate_bindings(source, DeviceBindings(devices=(binding(),))) == ()
    wrong = replace(binding(), contract=BASE_DEVICE_CONTRACT, base_contracts=(), writable_properties=(), supported_operations=())
    assert [d.code for d in validate_bindings(source, DeviceBindings(devices=(wrong,)))] == ["device_type"]
    assert [d.code for d in validate_bindings(program(), DeviceBindings(devices=(binding(),)))] == ["unknown_resource_binding"]
    with pytest.raises(TypeError, match="DeviceBindings"):
        validate_bindings(source, {})


def test_binding_facts_freeze_collections_and_reject_aliases():
    data = [binding()]
    bindings = DeviceBindings(devices=data)
    data.clear()
    assert len(bindings.devices) == 1
    with pytest.raises(ValueError, match="logical_id"):
        DeviceBindings(devices=(binding(), binding()))
    with pytest.raises(ValueError, match="physical_id"):
        DeviceBindings(devices=(binding(), replace(binding(), logical_id="other")))
    with pytest.raises(TypeError, match="DeviceBinding"):
        DeviceBindings(devices=("not a record",))
    with pytest.raises(ValueError, match="identities"):
        replace(binding(), contract=replace(AGITATOR_CONTRACT, base_type_ids=("  ",)))
