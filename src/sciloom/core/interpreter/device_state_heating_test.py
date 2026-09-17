"""Fixed thermal configuration shares generic effects without shaker state leaks."""

from dataclasses import replace

import pytest

from examples.developer.warm_sample_ir import BenchHeater, ThermalRecordingTarget, build_program
from examples.warm_sample import WarmSample
from sciloom import Agitator, Function, Heater, Input, Temperature, Var, Zone, degC, degC_per_min, log, rpm, runtime
from sciloom.conftest import StubShaker
from sciloom.core.bindings import DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError, IRValidationError
from sciloom.core.ir import ConfigureProperty, DeviceAt, DeviceCommand, ZoneLiteral, from_json, to_json
from sciloom.core.ir.device_contracts import HEATER_CONTRACT, START_HEATER_ID
from sciloom.devices import operation
from sciloom.devices.declarations import bind_device, device_contract
from sciloom_autosuite import AutoSuiteTarget
from . import DeviceEvent, Interpreter, ReferenceEnvironment, VirtualClock, WaitEvent


def test_author_direct_json_fixed_binding_wait_and_order():
    target = ThermalRecordingTarget()
    source = WarmSample().compile(target=target)
    direct = build_program()
    states = []
    for program in (source.semantic_ir, source.specialized_ir, direct, from_json(to_json(direct))):
        assert isinstance(program.functions[0].body[0], ConfigureProperty)
        assert isinstance(program.functions[0].body[2], DeviceCommand)
        clock = VirtualClock()
        result = Interpreter(
            program,
            environment=ReferenceEnvironment(
                clock=clock,
                device_bindings=target.resolve_devices(program),
            ),
        ).run()
        assert [type(event) for event in result.events] == [
            DeviceEvent,
            DeviceEvent,
            DeviceEvent,
            WaitEvent,
            DeviceEvent,
        ]
        assert result.events[2].state.enabled
        assert not result.events[-1].state.enabled
        assert clock.monotonic() == 10
        state = next(iter(result.resources.values()))
        assert (
            state.configuration
            == state.applied_configuration
            == {"temperature": 20 * degC, "ramp_rate": 1 * degC_per_min}
        )
        assert result.physical_devices["reference:heater-1"].applied_configuration == state.configuration
        states.append(state)
    assert all(state == states[0] for state in states)


def test_missing_clock_stops_before_explicit_stop_without_inventing_shutdown():
    program = build_program()
    env = ReferenceEnvironment(device_bindings=ThermalRecordingTarget().resolve_devices(program))
    with pytest.raises(ExecutionError, match="missing_environment_service"):
        Interpreter(program, environment=env).run()
    assert len(env.events) == 3
    assert env.events[-1].operation_id == START_HEATER_ID and env.events[-1].state.enabled


class ApplyHeat(Function):
    heater: Heater

    @runtime
    def run(self):
        self.heater.start()


class MixedDevices(Function):
    heater: Heater
    shaker: Agitator
    temperature: Var[Temperature] = 20 * degC

    def __init__(self):
        self.apply_heat = ApplyHeat()
        self.apply_heat.heater = self.heater

    @runtime
    def run(self):
        self.temperature = 20 * degC
        self.heater.temperature = self.temperature
        self.heater.ramp_rate = 1 * degC_per_min
        self.temperature = 25 * degC
        self.shaker.speed = 300 * rpm
        self.shaker.start()
        self.apply_heat()
        self.heater.temperature = self.temperature
        self.apply_heat()
        self.heater.ramp_rate = 2 * degC_per_min
        self.heater.stop()
        self.shaker.stop()


class MixedTarget(ThermalRecordingTarget):
    def resolve_devices(self, program):
        return DeviceBindings(
            devices=(
                bind_device(logical_id="heater", device=BenchHeater(), physical_id="reference:heater-1"),
                bind_device(logical_id="shaker", device=StubShaker(), physical_id="reference:shaker-1"),
            )
        )


def test_shared_cross_call_capture_reapply_stop_and_mixed_state():
    target = MixedTarget()
    compiled = MixedDevices().compile(target=target)
    for program in (compiled.semantic_ir, from_json(compiled.artifact.content.decode())):
        env = ReferenceEnvironment(device_bindings=target.resolve_devices(program))
        session = Interpreter(program, environment=env)
        first = session.run()
        heater = [event.state for event in first.events if event.resource_id == "resource:heater"]
        assert len(heater) == 7
        assert heater[1].configuration["temperature"] == 20 * degC and not heater[1].enabled
        assert heater[2].applied_configuration["temperature"] == 20 * degC and heater[2].enabled
        assert heater[3].configuration["temperature"] == 25 * degC
        assert heater[3].applied_configuration["temperature"] == 20 * degC
        assert heater[4].applied_configuration["temperature"] == 25 * degC
        assert heater[5].configuration["ramp_rate"] == 2 * degC_per_min and heater[5].enabled
        assert heater[5].applied_configuration["ramp_rate"] == 1 * degC_per_min
        assert heater[6].configuration == heater[5].configuration and not heater[6].enabled
        assert heater[6].applied_configuration == heater[4].applied_configuration
        assert first.resources["resource:shaker"].configuration == {"speed": 300 * rpm}
        assert first.physical_devices["reference:heater-1"].applied_configuration == heater[4].applied_configuration
        assert first.physical_devices["reference:shaker-1"].applied_configuration == {"speed": 300 * rpm}
        assert session.run().resources == first.resources
        assert heater[2].applied_configuration["temperature"] == 20 * degC
        with pytest.raises(TypeError):
            heater[2].configuration["temperature"] = 90 * degC
        with pytest.raises(ValueError, match="physical_id"):
            DeviceBindings(
                devices=(
                    env.device_bindings.devices[0],
                    replace(env.device_bindings.devices[1], physical_id="reference:heater-1"),
                )
            )


@pytest.mark.parametrize("temperature,rate", [(False, False), (False, True), (True, False)])
def test_both_required_properties_fail_before_following_effect(temperature, rate):
    class Missing(Function):
        heater: Heater

        def __init__(self):
            self.configure_temperature = temperature
            self.configure_rate = rate

        @runtime
        def run(self):
            if self.configure_temperature:
                self.heater.temperature = 20 * degC
            if self.configure_rate:
                self.heater.ramp_rate = 1 * degC_per_min
            self.heater.start()
            log("must not run", category="thermal", stream="after")

    target = ThermalRecordingTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        Missing().compile(target=target)
    program = Missing().to_ir()
    env = ReferenceEnvironment(device_bindings=target.resolve_devices(program))
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=env).run()
    assert len(env.events) == int(temperature) + int(rate)
    assert all(isinstance(event, DeviceEvent) and not event.state.enabled for event in env.events)


def test_branch_configuration_is_not_assumed_from_an_earlier_invocation():
    class Conditional(Function):
        heater: Heater
        configure: Input[bool]

        @runtime
        def run(self):
            if self.configure:
                self.heater.temperature = 20 * degC
                self.heater.ramp_rate = 1 * degC_per_min
            self.heater.start()

    target = ThermalRecordingTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        Conditional().compile(target=target)
    program = Conditional().to_ir()
    session = Interpreter(program, environment=ReferenceEnvironment(device_bindings=target.resolve_devices(program)))
    session.run(inputs={"configure": True})
    assert session.run(inputs={"configure": False}).resources["resource:heater"].enabled
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program).run(inputs={"configure": False})


def test_stop_needs_no_configuration_and_does_not_start():
    program = build_program()
    stop_only = replace(program, functions=(replace(program.functions[0], body=(program.functions[0].body[-1],)),))
    compiled = compile_ir(stop_only, target=ThermalRecordingTarget())
    result = Interpreter(compiled.specialized_ir).run()
    state = result.resources["heater"]
    assert not state.enabled and state.configuration == state.applied_configuration == {}


@pytest.mark.parametrize("writable", [(), ("temperature", "ramp_rate")])
def test_derived_profile_cannot_waive_heater_start_requirements(writable):
    class RelaxedProfile(Heater):
        device_type_id = "test.relaxed-heater/v1"
        writable_properties = writable
        required_configuration = ()
        supported_operations = (Heater.start, Heater.stop)

    if not writable:
        with pytest.raises(ValueError, match="lifecycle command configuration"):
            bind_device(logical_id="heater", device=RelaxedProfile(), physical_id="reference:relaxed")
        return

    class RelaxedTarget(ThermalRecordingTarget):
        def resolve_devices(self, program):
            return DeviceBindings(
                devices=(bind_device(logical_id="heater", device=RelaxedProfile(), physical_id="reference:relaxed"),)
            )

    target = RelaxedTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        ApplyHeat().compile(target=target)
    program = ApplyHeat().to_ir()
    environment = ReferenceEnvironment(device_bindings=target.resolve_devices(program))
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=environment).run()
    assert environment.events == ()
    # Waiving profile-specific extras remains valid once both family settings exist.
    compiled = WarmSample().compile(target=target)
    state = (
        Interpreter(
            compiled.specialized_ir,
            environment=ReferenceEnvironment(clock=VirtualClock(), device_bindings=target.resolve_devices(program)),
        )
        .run()
        .resources["resource:heater"]
    )
    assert state.configuration == {"temperature": 20 * degC, "ramp_rate": 1 * degC_per_min}


def test_zero_iteration_configuration_does_not_satisfy_start():
    class LoopConfigured(Function):
        heater: Heater
        again: Input[bool]

        @runtime
        def run(self):
            self.heater.temperature = 20 * degC
            while self.again:
                self.heater.ramp_rate = 1 * degC_per_min
                self.again = False
            self.heater.start()

    target = ThermalRecordingTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        LoopConfigured().compile(target=target)
    program = LoopConfigured().to_ir()
    for again in (True, False):
        session = Interpreter(
            program, environment=ReferenceEnvironment(device_bindings=target.resolve_devices(program))
        )
        if again:
            assert session.run(inputs={"again": True}).resources["resource:heater"].enabled
        else:
            with pytest.raises(ExecutionError, match="device_configuration"):
                session.run(inputs={"again": False})


def test_independent_child_cannot_borrow_parent_heater_configuration():
    class Independent(Function):
        heater: Heater

        def __init__(self):
            self.child = ApplyHeat()

        @runtime
        def run(self):
            self.heater.temperature = 20 * degC
            self.heater.ramp_rate = 1 * degC_per_min
            self.child()
            self.heater.start()

    class SeparateTarget(ThermalRecordingTarget):
        def resolve_devices(self, program):
            return DeviceBindings(
                devices=(
                    bind_device(logical_id="heater", device=BenchHeater(), physical_id="reference:parent"),
                    bind_device(logical_id="child.heater", device=BenchHeater(), physical_id="reference:child"),
                )
            )

    target = SeparateTarget()
    with pytest.raises(CompilationError, match="device_configuration"):
        Independent().compile(target=target)
    program = Independent().to_ir()
    env = ReferenceEnvironment(device_bindings=target.resolve_devices(program))
    with pytest.raises(ExecutionError, match="device_configuration"):
        Interpreter(program, environment=env).run()
    assert len(env.events) == 2
    assert all(not event.state.enabled for event in env.events)


def test_heater_extension_adds_configuration_without_changing_family():
    class TunableHeater(Heater):
        device_type_id = "test.tunable-heater/v1"
        writable_properties = ("temperature", "ramp_rate", "gain")
        required_configuration = ("temperature", "ramp_rate", "gain")
        supported_operations = (Heater.start, Heater.stop)

        @property
        def gain(self) -> float:
            pytest.fail("getter cannot run")

        @gain.setter
        @operation(id="test.tunable-heater.gain/v1")
        def gain(self, value: float) -> None:
            pytest.fail("setter cannot run")

    binding = bind_device(logical_id="heater", device=TunableHeater(), physical_id="reference:heater-2")
    assert device_contract(Heater) == HEATER_CONTRACT
    assert len(binding.contract.required_configuration) == 3

    class ExtensionTarget(ThermalRecordingTarget):
        def resolve_devices(self, program):
            return DeviceBindings(devices=(binding,))

    with pytest.raises(CompilationError, match="device_configuration"):
        WarmSample().compile(target=ExtensionTarget())

    class ExtendedWarm(Function):
        heater: TunableHeater

        @runtime
        def run(self):
            self.heater.temperature = 30 * degC
            self.heater.ramp_rate = 2 * degC_per_min
            self.heater.gain = 0.5
            self.heater.start()
            self.heater.stop()

    compiled = ExtendedWarm().compile(target=ExtensionTarget())
    state = Interpreter(from_json(compiled.artifact.content.decode())).run().resources["resource:heater"]
    assert state.applied_configuration == {"temperature": 30 * degC, "ramp_rate": 2 * degC_per_min, "gain": 0.5}
    assert not state.enabled


@pytest.mark.parametrize("profile", [Heater, BenchHeater])
@pytest.mark.parametrize("scoped", [False, True])
def test_thermal_candidate_selection_and_native_profile_remain_gated(profile, scoped):
    program = build_program()
    if scoped:
        function = program.functions[0]
        program = replace(
            program,
            functions=(
                replace(
                    function,
                    body=(
                        DeviceAt(
                            node_id="at",
                            resource_id="heater",
                            location=ZoneLiteral(node_id="zone", well_ids=("a",)),
                            body=function.body,
                        ),
                    ),
                ),
            ),
        )
    fixed = bind_device(logical_id="heater", device=profile(), physical_id="reference:fixed")
    candidates = DeviceBindings(
        devices=(
            DeviceSelectionBinding(
                logical_id="heater", candidates=(DeviceCandidate(binding=fixed, wells=Zone(well_ids=("a",))),)
            ),
        )
    )

    class DynamicTarget(ThermalRecordingTarget):
        def resolve_devices(self, program):
            return candidates

    with pytest.raises(CompilationError, match="unsupported_thermal_selection"):
        compile_ir(program, target=DynamicTarget())
    with pytest.raises(IRValidationError, match="unsupported_thermal_selection"):
        Interpreter(program, environment=ReferenceEnvironment(device_bindings=candidates))
    # Derived BenchHeater is covered above; fixed native emission is still rejected.
    codes = {d.code for d in AutoSuiteTarget().validate(program)}
    assert {"unsupported_temperature_type", "unsupported_device_command"} <= codes
