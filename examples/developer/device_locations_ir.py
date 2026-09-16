"""For developers: keep logical configuration separate from two physical shakers.

Run: ``uv run python -m examples.developer.device_locations_ir``
Expected terminal output:
    device_locations_ir.json
    shaker:A: running=True, speed=300 rpm
    shaker:B: running=False, speed=600 rpm

The complete JSON v4 program is device_locations_ir.json. Deployment facts and
the location directory are supplied separately after restoring it. Scope exit
does not stop A; B receives a new configuration and an explicit stop. These are
reference results, with synthetic identities and no hardware I/O. AutoSuite
dynamic emission remains gated on native runtime-failure validation.
"""

from pathlib import Path

from sciloom.core.bindings import DeviceBinding, DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment
from sciloom.core.ir import (
    ConfigureProperty,
    DeviceAt,
    DeviceResource,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    StartAgitation,
    StopAgitation,
    Variable,
    VariableRole,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.ir.device_contracts import (
    AGITATION_SPEED_ID,
    AGITATOR_CONTRACT,
    BASE_DEVICE_CONTRACT,
    START_AGITATION_ID,
    STOP_AGITATION_ID,
)
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom.core.specialization import specialize
from sciloom.units import RotationalSpeed, rpm


def build_program() -> Program:
    """Build two captured locations and independent lifecycle actions."""
    return Program(
        entry_function_id="select",
        resources=(DeviceResource(node_id="mixer", logical_id="mixer", device_type_id=AGITATOR_CONTRACT.type_id),),
        device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT),
        functions=(
            FunctionIR(
                node_id="select",
                name="SelectShakers",
                variables=tuple(
                    Variable(node_id=name, owner_id="select", name=name, type=ZoneType(), role=VariableRole.INPUT)
                    for name in ("first", "second")
                ),
                body=(
                    ConfigureProperty(
                        node_id="save-first",
                        resource_id="mixer",
                        property_id=AGITATION_SPEED_ID,
                        value=Literal(node_id="speed-first", type=ScalarType.ROTATIONAL_SPEED, value=5.0),
                    ),
                    DeviceAt(
                        node_id="at-first",
                        resource_id="mixer",
                        location=Reference(node_id="first-location", symbol_id="first"),
                        body=(StartAgitation(node_id="start-first", resource_id="mixer"),),
                    ),
                    ConfigureProperty(
                        node_id="save-second",
                        resource_id="mixer",
                        property_id=AGITATION_SPEED_ID,
                        value=Literal(node_id="speed-second", type=ScalarType.ROTATIONAL_SPEED, value=10.0),
                    ),
                    DeviceAt(
                        node_id="at-second",
                        resource_id="mixer",
                        location=Reference(node_id="second-location", symbol_id="second"),
                        body=(
                            StartAgitation(node_id="start-second", resource_id="mixer"),
                            StopAgitation(node_id="stop-second", resource_id="mixer"),
                        ),
                    ),
                ),
            ),
        ),
    )


def example_environment() -> ReferenceEnvironment:
    """Bind one logical mixer to either synthetic controller, with explicit wells."""
    candidates = tuple(
        DeviceCandidate(
            binding=DeviceBinding(
                logical_id="mixer",
                physical_id=f"shaker:{name}",
                contract=AGITATOR_CONTRACT,
                base_contracts=(BASE_DEVICE_CONTRACT,),
                writable_properties=(AGITATION_SPEED_ID,),
                supported_operations=(START_AGITATION_ID, STOP_AGITATION_ID),
            ),
            wells=Zone(well_ids=(f"well:{name}",)),
        )
        for name in ("A", "B")
    )
    return ReferenceEnvironment(
        device_bindings=DeviceBindings(devices=(DeviceSelectionBinding(logical_id="mixer", candidates=candidates),)),
        locations=LocationDirectory(wells=tuple(Well(identity=f"well:{name}", name=name) for name in ("A", "B"))),
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    env = example_environment()
    assert env.device_bindings is not None
    program = specialize(restored, bindings=env.device_bindings)
    result = Interpreter(program, environment=env).run(
        inputs={"first": Zone(well_ids=("well:A",)), "second": Zone(well_ids=("well:B",))}
    )
    print(path.name)
    for identity, state in result.physical_devices.items():
        speed = state.applied_configuration["speed"]
        assert isinstance(speed, RotationalSpeed)
        print(f"{identity}: running={state.enabled}, speed={speed / rpm:g} rpm")
