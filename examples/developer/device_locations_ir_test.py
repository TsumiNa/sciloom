"""The direct location program survives JSON and deployment rebinding unchanged."""

from dataclasses import replace
from pathlib import Path

from sciloom.core.bindings import DeviceBindings
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import Zone
from sciloom.core.specialization import specialize
from sciloom.units import rpm
from .device_locations_ir import build_program, example_environment


def test_direct_ir_companion_and_rebinding():
    program = build_program()
    companion = Path(__file__).with_name("device_locations_ir.json").read_text()
    assert companion == to_json(program)
    restored = from_json(companion)
    original = example_environment()
    (selection,) = original.device_bindings.devices
    rebound = replace(
        selection,
        candidates=tuple(
            replace(c, binding=replace(c.binding, physical_id="replacement:" + c.binding.physical_id))
            for c in selection.candidates
        ),
    )
    for env in (original, replace(original, device_bindings=DeviceBindings(devices=(rebound,)))):
        selected = specialize(restored, bindings=env.device_bindings)
        result = Interpreter(selected, environment=env).run(
            inputs={"first": Zone(well_ids=("well:A",)), "second": Zone(well_ids=("well:B",))}
        )
        a, b = result.physical_devices.values()
        assert a.enabled and not b.enabled
        assert a.applied_configuration == {"speed": 300 * rpm}
        assert b.applied_configuration == {"speed": 600 * rpm}
    assert to_json(restored) == companion
