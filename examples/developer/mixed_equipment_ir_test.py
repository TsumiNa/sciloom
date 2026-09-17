"""Integrated source/IR/JSON behavior, explicit failures and truthful native gates."""

import hashlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

from examples.agitation import ConfigureAgitation
from examples.capture_barcode import CaptureBarcode
from examples.mixed_equipment import MixedEquipment
from examples.transfer_sample import TransferSample
from examples.warm_sample import WarmSample
from sciloom import mL, mL_per_min, s
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError
from sciloom.core.interpreter import (
    DeviceEvent,
    DialogEvent,
    DialogOutcome,
    DialogResponse,
    Interpreter,
    LogEvent,
    QueuedDialogResponses,
    ReferenceEnvironment,
    TransferEvent,
    VirtualClock,
    WaitEvent,
    WellProperties,
    WellPropertyWriteEvent,
)
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import Zone
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget, write_autosuite_review
from .barcode_ir import build_program as barcode_program
from .mixed_equipment_ir import MixedRecordingTarget, reference_environment
from .runtime_workflows_ir import ReferenceArchiveTarget
from .source_paths import repository_relative
from .transfer_sample_ir import (
    DESTINATION,
    LOCATIONS,
    SOURCE,
    TransferRecordingTarget,
    build_program as transfer_program,
)
from .warm_sample_ir import ThermalRecordingTarget, build_program as heater_program


def trace(events):
    return tuple(
        (
            type(event).__name__,
            {
                field.name: getattr(event, field.name)
                for field in fields(event)
                if field.name not in {"node_id", "resource_id"}
                and (field.name != "source" or isinstance(getattr(event, field.name), Zone))
            },
        )
        for event in events
    )


@pytest.mark.parametrize(
    "author,builder,target,inputs,kinds,gates",
    [
        (
            CaptureBarcode,
            barcode_program,
            ReferenceArchiveTarget(),
            {"well": DESTINATION},
            (DialogEvent, WellPropertyWriteEvent, LogEvent),
            {"unsupported_dialog_result", "unsupported_zone_cardinality"},
        ),
        (
            WarmSample,
            heater_program,
            ThermalRecordingTarget(),
            {},
            (DeviceEvent, DeviceEvent, DeviceEvent, WaitEvent, DeviceEvent),
            {"unsupported_temperature_type", "unsupported_device_command"},
        ),
        (
            TransferSample,
            transfer_program,
            TransferRecordingTarget(),
            {"source": SOURCE, "destination": DESTINATION},
            (DeviceEvent, DeviceEvent, DeviceEvent, TransferEvent, LogEvent),
            {"unsupported_transfer_quantity", "unsupported_device_command"},
        ),
    ],
)
def test_three_required_flows_agree_across_all_forms(author, builder, target, inputs, kinds, gates, tmp_path):
    expected = None
    authored = author().to_ir()
    direct = builder()
    for program in (authored, direct, from_json(to_json(authored)), from_json(to_json(direct))):
        before = to_json(program)
        compiled = compile_ir(program, target=target)
        env = ReferenceEnvironment(
            device_bindings=target.resolve_devices(program),
            locations=LOCATIONS,
            clock=VirtualClock(),
            properties=WellProperties(),
            dialogs=QueuedDialogResponses((DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"),)),
        )
        result = Interpreter(from_json(compiled.artifact.content.decode()), environment=env).run(inputs=inputs)
        assert tuple(type(event) for event in result.events) == kinds
        actual = (result.outputs, trace(result.events), env.clock.monotonic(), env.properties.snapshot())
        if expected is None:
            expected = actual
        assert actual == expected
        assert compiled.semantic_ir == program and to_json(program) == before
        assert gates <= {d.code for d in AutoSuiteTarget().validate(program)}
        path = tmp_path / "gated.asfp"
        with pytest.raises(CompilationError):
            compile_ir(program, target=AutoSuiteTarget()).write(path)
        assert not path.exists()


def test_mixed_child_configuration_order_restart_and_immutable_snapshots():
    program = repository_relative(MixedEquipment().to_ir())
    compiled = compile_ir(program, target=MixedRecordingTarget())
    assert len(compiled.semantic_ir.resources) == 3  # Shared child adds no duplicate devices.
    expected = None
    for candidate in (program, compiled.specialized_ir, from_json(compiled.artifact.content.decode())):
        env = reference_environment(
            candidate,
            responses=(
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"),
                DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-002"),
            ),
        )
        session = Interpreter(candidate, environment=env)
        result = session.run(inputs={"source": SOURCE, "destination": DESTINATION})
        assert result.outputs == {"barcode": "S-001"}
        assert env.properties.snapshot() == {("well:destination", "sample_ID"): "S-001"}
        assert [type(e) for e in result.events] == (
            [DialogEvent, WellPropertyWriteEvent, LogEvent]
            + [DeviceEvent] * 6
            + [DeviceEvent, DeviceEvent, WaitEvent, TransferEvent, DeviceEvent, DeviceEvent, LogEvent]
            + [DeviceEvent]
            + [DeviceEvent, DeviceEvent, WaitEvent, TransferEvent, DeviceEvent, DeviceEvent, LogEvent]
        )
        transfers = [e for e in result.events if isinstance(e, TransferEvent)]
        assert [e.configuration["aspirate_flow"] for e in transfers] == [1 * mL_per_min, 3 * mL_per_min]
        assert all(e.source == SOURCE and e.destination == DESTINATION for e in transfers)
        assert env.clock.monotonic() == 20
        assert not any(state.enabled for state in result.resources.values())
        assert not any(state.enabled for state in result.physical_devices.values())
        assert set(result.physical_devices) == {"reference:heater-1", "reference:shaker-1", "reference:liquid-1"}
        current = trace(result.events)
        if expected is None:
            expected = current
        assert current == expected
        old_history = env.events
        second = session.run(inputs={"source": SOURCE, "destination": DESTINATION})
        assert second.outputs == {"barcode": "S-002"} and env.clock.monotonic() == 40
        assert len(env.events) == 2 * len(old_history)
        assert old_history == result.events
        assert [e.configuration["aspirate_flow"] for e in transfers] == [1 * mL_per_min, 3 * mL_per_min]
        assert second.resources == result.resources
        with pytest.raises(TypeError):
            transfers[0].configuration["aspirate_flow"] = 9 * mL_per_min
        restarted = reference_environment(
            candidate, responses=(DialogResponse(outcome=DialogOutcome.ACCEPTED, value="restart"),)
        )
        assert (
            Interpreter(candidate, environment=restarted)
            .run(inputs={"source": SOURCE, "destination": DESTINATION})
            .resources
            == result.resources
        )


@pytest.mark.parametrize(
    "response",
    [
        DialogResponse(outcome=DialogOutcome.CANCELLED),
        DialogResponse(outcome=DialogOutcome.STOPPED),
        DialogResponse(outcome=DialogOutcome.TIMED_OUT),
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value="late", elapsed=30 * s),
        DialogResponse(outcome=DialogOutcome.ACCEPTED, value=False),
    ],
)
def test_dialog_failure_in_full_flow_prevents_metadata_and_every_device_effect(response):
    program = MixedEquipment().to_ir()
    for candidate in (program, from_json(to_json(program))):
        env = reference_environment(candidate, responses=(response,))
        with pytest.raises(ExecutionError, match="dialog_"):
            Interpreter(candidate, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
        assert env.properties.snapshot() == {} and env.clock.monotonic() == 0
        assert len(env.events) == 1 and isinstance(env.events[0], DialogEvent)


def test_missing_response_and_invalid_destination_are_not_accepted_implicitly():
    program = MixedEquipment().to_ir()
    env = reference_environment(program, responses=())
    with pytest.raises(ExecutionError, match="dialog_"):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert env.events == () and env.properties.snapshot() == {}
    env = reference_environment(program, responses=(DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"),))
    with pytest.raises(ExecutionError):
        Interpreter(program, environment=env).run(inputs={"source": SOURCE, "destination": Zone.empty()})
    assert env.events == () and env.dialogs.remaining == 1


def test_transfer_failure_preserves_earlier_effects_without_synthetic_stop_or_success_log():
    program = MixedEquipment().to_ir()
    env = reference_environment(program, responses=(DialogResponse(outcome=DialogOutcome.ACCEPTED, value="S-001"),))
    original = env.device_bindings.devices
    env = replace(
        env, device_bindings=DeviceBindings(devices=(*original[:2], replace(original[2], usable_capacity=0.1 * mL)))
    )
    session = Interpreter(program, environment=env)
    with pytest.raises(ExecutionError, match="transfer_capacity"):
        session.run(inputs={"source": SOURCE, "destination": DESTINATION})
    assert env.properties.snapshot() == {("well:destination", "sample_ID"): "S-001"}
    assert env.clock.monotonic() == 10
    assert not any(isinstance(event, TransferEvent) for event in env.events)
    assert [e.value for e in env.events if isinstance(e, LogEvent)] == ["S-001"]
    assert session._devices.physical["reference:heater-1"].enabled
    assert session._devices.physical["reference:shaker-1"].enabled
    assert session._devices.physical["reference:liquid-1"].applied_configuration == {}


def test_real_actuator_collision_cannot_be_hidden_by_family_or_logical_names():
    bindings = MixedRecordingTarget().resolve_devices(MixedEquipment().to_ir())
    heater, shaker, liquid = bindings.devices
    with pytest.raises(ValueError, match="physical_id"):
        DeviceBindings(
            devices=(heater, shaker, replace(liquid, binding=replace(liquid.binding, physical_id=heater.physical_id)))
        )


def test_reference_companion_is_reproducible_and_never_a_native_review_bundle(tmp_path):
    program = repository_relative(MixedEquipment().to_ir())
    result = compile_ir(program, target=MixedRecordingTarget())
    assert result.artifact.media_type == "application/json" and result.artifact.suffix == ".json"
    assert Path(__file__).with_name("mixed_equipment_ir.json").read_bytes() == result.artifact.content
    with pytest.raises(ValueError, match="target identity"):
        write_autosuite_review(result, target=AutoSuiteTarget(), path=tmp_path / "mixed.asfp")
    assert list(tmp_path.iterdir()) == []


def test_existing_native_shaker_review_still_includes_explicit_deployment_conditions(tmp_path):
    target = AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})
    compiled = ConfigureAgitation().compile(target=target)
    path = tmp_path / "shaker.asfp"
    report = write_autosuite_review(compiled, target=target, path=path)
    assert path.read_bytes() == Path(__file__).parents[1].joinpath("agitation.asfp").read_bytes()
    assert path.with_suffix(".deployment.json").read_text() == report.to_json()
    assert report.status.value == "unknown" and report.native_status == "pending"
    assert report.requirements and report.findings
    assert report.artifact_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert report.specialized_ir_sha256 == hashlib.sha256(to_json(compiled.specialized_ir).encode()).hexdigest()
