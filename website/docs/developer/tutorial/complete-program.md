# 8. The complete program

The seven steps, in order, are this file. Paste it into your own package,
run it, and you have a family, two profiles, a target, five rejections, an
adaptive program and a reference execution. The documentation tests run this
listing and prove it equals the steps on the previous pages.

```python
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from sciloom import Function, Input, Output, comptime, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import CompilationError, Diagnostic, DiagnosticError, ExecutionError, IRValidationError
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import DeviceCommand, Literal, Program, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.devices import BaseDevice, operation
from sciloom.devices.declarations import bind_device, device_contract

HOLD_ID = "example.heater.hold/v1"


class Heater(BaseDevice):
    """A device family: what every heater can be asked to do."""

    device_type_id: ClassVar[str] = "example.heater/v1"

    @property
    def setpoint(self) -> float:
        raise TypeError("Device property reads are not supported yet.")

    @setpoint.setter
    @operation(id="example.heater.setpoint/v1")
    def setpoint(self, value: float) -> None:
        """Save the target temperature to apply when heating starts."""

    @operation(id=HOLD_ID)
    def hold(self, seconds: float) -> None:
        """Hold the saved setpoint for a duration."""


family = device_contract(Heater)
print("family:", family.type_id, "extends", list(family.base_type_ids))
print("properties:", [prop.semantic_id for prop in family.properties])
print("commands:", [command.semantic_id for command in family.operations])

@dataclass(frozen=True, kw_only=True)
class BenchHeater(Heater):
    """A bench heater whose setpoint can be written."""

    channel: str = "A"
    device_type_id: ClassVar[str] = "example.bench-heater/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ("setpoint",)
    required_configuration: ClassVar[tuple[str, ...]] = ("setpoint",)
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (Heater.hold,)


@dataclass(frozen=True, kw_only=True)
class FixedHeater(Heater):
    """A heater wired to a fixed temperature; nothing can be written to it."""

    channel: str = "B"
    device_type_id: ClassVar[str] = "example.fixed-heater/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ()
    required_configuration: ClassVar[tuple[str, ...]] = ()
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (Heater.hold,)


for profile in (BenchHeater(), FixedHeater()):
    binding = bind_device(logical_id="heater", device=profile, physical_id=f"bench:{profile.channel}")
    print(f"{type(profile).__name__}: writes {list(binding.writable_properties)}, runs {list(binding.supported_operations)}")


class LazyHeater(Heater):
    """A profile that forgets to declare its capabilities."""

    device_type_id: ClassVar[str] = "example.lazy-heater/v1"


try:
    bind_device(logical_id="heater", device=LazyHeater(), physical_id="bench:?")
except TypeError as error:
    print("inherited lists:", error)

class Anneal(Function):
    """Set a temperature and hold it.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        done: Set once the hold has been requested.
    """

    heater: Heater
    temperature: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        self.heater.setpoint = self.temperature
        self.heater.hold(30.0)
        self.done = True


program = Anneal().to_ir()
print("nodes:", ", ".join(type(node).__name__ for node in program.functions[0].body))
print("resources:", [resource.logical_id for resource in program.resources])
print("contracts:", [contract.type_id for contract in program.device_types])

class BenchTarget:
    """Record the selected program as JSON, within one bench's proven limits."""

    target_id = "example.bench/v1"
    max_hold_seconds = 600.0

    def __init__(self, *, devices: Mapping[str, BenchHeater | FixedHeater]) -> None:
        if any(type(device) not in (BenchHeater, FixedHeater) for device in devices.values()):
            raise TypeError("BenchTarget supports BenchHeater and FixedHeater profiles.")
        if any(not device.channel for device in devices.values()):
            raise ValueError("Bench channels must not be empty.")
        self.devices = MappingProxyType(dict(devices))
        self.calls: list[str] = []

    def resolve_devices(self, program: Program) -> DeviceBindings:
        self.calls.append("resolve_devices")
        return DeviceBindings(
            devices=tuple(
                bind_device(logical_id=name, device=device, physical_id=f"bench:{device.channel}")
                for name, device in self.devices.items()
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        self.calls.append("validate")
        diagnostics = []
        for node, path in iter_nodes(program):
            if not (isinstance(node, DeviceCommand) and node.operation_id == HOLD_ID):
                continue
            seconds = node.arguments[0].value
            if not isinstance(seconds, Literal) or not isinstance(seconds.value, int | float):
                diagnostics.append(
                    self.rejected(node, path, "hold() requires a literal duration; this target proves literals only.")
                )
            elif not 0.0 <= seconds.value <= self.max_hold_seconds:
                diagnostics.append(
                    self.rejected(node, path, f"hold() must be within [0, {self.max_hold_seconds}] s on this bench.")
                )
        return tuple(diagnostics)

    def rejected(self, node: DeviceCommand, path: str, message: str) -> Diagnostic:
        return Diagnostic(
            code="bench_hold_limit",
            message=message,
            path=path,
            node_id=node.node_id,
            source=node.source,
        )

    def emit(self, program: Program) -> Artifact:
        self.calls.append("emit")
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")


target = BenchTarget(devices={"heater": BenchHeater()})
result = Anneal().compile(target=target)
print("pipeline:", " -> ".join(target.calls))
print("target:", result.target_id, "artifact:", result.artifact.media_type)
print("selected contracts:", [contract.type_id for contract in result.specialized_ir.device_types])

def report(label: str, error: DiagnosticError) -> None:
    diagnostic = error.diagnostics[0]
    attached = " (source attached)" if diagnostic.source is not None else ""
    print(f"{label}: {type(error).__name__} [{diagnostic.code}]{attached}")
    print(f"    {diagnostic.message}")


class RuntimeHold(Function):
    """Hold for a caller-selected duration, which this target cannot prove.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        seconds: Hold duration supplied by the caller.
        done: Set once the hold has been requested.
    """

    heater: Heater
    temperature: Input[float]
    seconds: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        self.heater.setpoint = self.temperature
        self.heater.hold(self.seconds)
        self.done = True


try:

    class SlotWithValue(Function):
        heater: Heater = BenchHeater()
        done: Output[bool]

        @runtime
        def run(self) -> None:
            self.done = True

    raise AssertionError("a class-level device value should be rejected")
except IRValidationError as error:
    report("declaration", error)


class ReadsBack(Function):
    """Try to read a device property back, which the source subset forbids.

    Attributes:
        heater: Logical heater bound by the selected target.
        value: Where the read value would go.
    """

    heater: Heater
    value: Output[float]

    @runtime
    def run(self) -> None:
        self.value = self.heater.setpoint


try:
    ReadsBack().to_ir()
    raise AssertionError("a device property read should be rejected")
except IRValidationError as error:
    report("source", error)

try:
    RuntimeHold().compile(target=BenchTarget(devices={"heater": FixedHeater()}))
    raise AssertionError("writing to a fixed heater should be rejected")
except CompilationError as error:
    report("capability", error)

try:
    RuntimeHold().compile(target=BenchTarget(devices={"heater": BenchHeater()}))
    raise AssertionError("an unprovable hold duration should be rejected")
except CompilationError as error:
    report("platform", error)

try:
    BenchTarget(devices={"heater": BenchHeater(channel="")})
    raise AssertionError("an empty channel should be rejected")
except ValueError as error:
    print("deployment:", error)

class Adaptive(Function):
    """Write a setpoint only on a heater that accepts one.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        done: Set once the hold has been requested.
    """

    heater: Heater
    temperature: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        if comptime.can_write(self.heater, "setpoint"):
            self.heater.setpoint = self.temperature
        self.heater.hold(30.0)
        self.done = True


for label, profile in (("a writable heater", BenchHeater()), ("a read-only heater", FixedHeater())):
    selected = Adaptive().compile(target=BenchTarget(devices={"heater": profile})).specialized_ir
    print(f"adaptive on {label}:", ", ".join(type(node).__name__ for node in selected.functions[0].body))

try:
    Interpreter(result.specialized_ir).run(inputs={"temperature": 60.0})
except ExecutionError as error:
    print("interpreter:", error.diagnostics[0].code, error.diagnostics[0].message)


class Preheat(Function):
    """Save a setpoint; every statement has reference semantics.

    Attributes:
        heater: Logical heater bound by the selected target.
        temperature: Target temperature supplied by the caller.
        done: Set once the setpoint is saved.
    """

    heater: Heater
    temperature: Input[float]
    done: Output[bool]

    @runtime
    def run(self) -> None:
        self.heater.setpoint = self.temperature
        self.done = True


selected = Preheat().compile(target=BenchTarget(devices={"heater": BenchHeater()})).specialized_ir
snapshot = Interpreter(selected).run(inputs={"temperature": 60.0})
print("preheat:", snapshot.outputs["done"], dict(snapshot.resources["resource:heater"].configuration))
```

Where next: the [independent device example](../../examples/demo-device.md) is
the committed counterpart, a profile of a shipped family with a target; the
[Target contract](../reference/target-contract.md) and
[device contracts](../reference/device-contracts.md) state the rules this
series applied.
