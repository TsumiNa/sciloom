# Reject a program before it runs

A program can be wrong in many ways, and SciLoom answers at the earliest layer that
can prove it wrong. Knowing which layer speaks tells you where your own check
belongs, and why some mistakes are caught while you are still typing the class and
others only once a target is chosen.

This page continues the heater from [add a device](add-a-device.md) and the target
from [add a target](add-a-target.md).

## The layers, in order

| When | What it proves | Raises |
| --- | --- | --- |
| The class body runs | Declarations are well formed: field roles, device slots, device contracts | `IRValidationError` |
| `to_ir()` | The runtime method is in the supported source subset and types agree | `IRValidationError` |
| `compile_ir` starts | The IR itself is structurally valid, whatever produced it | `IRValidationError` |
| `resolve_devices` | Your deployment data is the kind you support | Your own `TypeError` or `ValueError` |
| Bindings are checked | Every bound profile implements what the program does with it | `CompilationError` |
| Configuration is checked | A lifecycle start has its required configuration on every reachable path | `CompilationError` |
| `Target.validate` | The program fits your platform | `CompilationError` |
| Reference execution | The program has defined semantics to simulate | `ExecutionError` |

Each layer only knows what it can see. The class body has no target, so it cannot
know your heater is read-only. The target has no Python source, so it cannot know
which variable the author called `seconds`, only that the argument is not a literal.
That is why a diagnostic carries a source span: the layer that proves the problem is
rarely the layer the author was thinking about.

## The first four layers, by example

A device slot with a class-level value never becomes a class:

```text
declaration: IRValidationError [class_schema]
    Device slot 'heater' cannot have a class-level value.
```

Reading a device property is outside the source subset, and lowering says so with
the author's own line attached:

```text
source: IRValidationError [device_property_read] (source attached)
    Device getters are not supported; use a runtime variable for the configured value.
```

Writing to a heater whose profile declares no writable properties compiles fine
until a target binds that profile:

```text
capability: CompilationError [device_capability] (source attached)
    The bound device does not implement this writable property contract.
```

And a duration this target cannot prove is rejected by the target itself:

```text
platform: CompilationError [bench_hold_limit] (source attached)
    hold() requires a literal duration; this target proves literals only.
```

The same authored program produced the last two: `RuntimeHold`, compiled once
against a fixed heater and once against a writable one. Nothing about the program
changed; the deployment did. This is the point of compiling against explicit bindings rather than against
an assumed instrument.

## Reading a diagnostic

Every rejection carries the same record.

| Field | Use |
| --- | --- |
| `code` | The rule that fired, stable enough to search for or match in a test |
| `message` | What is wrong, in the author's vocabulary |
| `path` | Where in the program, as a semantic path such as `$.functions[0].body[1]` |
| `node_id` | The exact node, for tooling that maps back to a graph |
| `source` | The author's Python file and line, when the program came from source |

The aggregating layers carry **all** the diagnostics they found, not the first, so
an author can fix a batch rather than recompile once per mistake. IR validation,
the binding and configuration checks and `Target.validate` all collect. Declaration
and source analysis raise at the first problem, because a half-built class or an
unparsable method makes everything after it meaningless.

## Where your own check belongs

Ask what the check actually knows about.

**A declaration.** Nothing to add: declaring a capability list wrong, naming a slot
after a host member, or omitting a versioned identity is already rejected when the
class body runs. Your job is to declare honestly.

**Your deployment data.** Check it in the target's `__init__` and raise an ordinary
`TypeError` or `ValueError`. The author is holding the wrong profile, and they find
out at the line that built the target.

**The program on your platform.** That is `Target.validate`. Return diagnostics,
one per rule, with your own code. Reject only what you can prove, and say in the
message what would be accepted.

**Something the program should survive.** Do not reject at all: let the program
adapt.

## Adapting instead of rejecting

A compile-time query asks about the bound device and keeps only the branch that
applies. Both branches are type-checked first, so the branch you did not take is
still valid code.

```python
    @runtime
    def run(self) -> None:
        if comptime.can_write(self.heater, "setpoint"):
            self.heater.setpoint = self.temperature
        self.heater.hold(30.0)
        self.done = True
```

The same source compiles for both profiles, and the configuration write simply is
not in the program for the read-only one:

```text
adaptive on a writable heater: ConfigureProperty, DeviceCommand, Assignment
adaptive on a read-only heater: DeviceCommand, Assignment
```

`can_write` asks about a property, `supports` about a command, and `is_device`
narrows to a specific profile type. They are compile-time questions only: their
arguments cannot depend on runtime values, and they are recognized in `if` and
`elif` conditions, nowhere else.

Use this when a program is genuinely correct on both kinds of instrument. Do not
use it to paper over a deployment that cannot run the experiment; a rejection the
author can read is better than a program that silently does less than they wrote.

## Writing a rejection the author can act on

The diagnostic in the example above says three things in one line: the rule
(`hold()` has a limit), the reason it fired (the argument is not a literal), and
what this target is capable of proving (literals only). An author can act on it
without reading your source.

Compare `invalid hold`, which says only that you are unhappy.

Give each rule its own `code` and keep the code stable. `path` is required; take it
from the traversal. `node_id` and `source` are optional, so attach them from the
node you rejected whenever it has them. Programmatically built IR may carry no
source at all, which is exactly why a message has to stand on its own.

A target that returns a single `Diagnostic(code="error", message="cannot compile",
path="$")` is technically valid and practically useless.

## The complete example

```python
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from sciloom import Function, Input, Output, comptime, runtime
from sciloom.core.compiler import Artifact
from sciloom.core.bindings import DeviceBindings
from sciloom.core.diagnostics import CompilationError, Diagnostic, DiagnosticError, IRValidationError
from sciloom.core.ir import DeviceCommand, Literal, Program, to_json
from sciloom.core.ir.traversal import iter_nodes
from sciloom.devices import BaseDevice, operation
from sciloom.devices.declarations import bind_device

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

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(
            devices=tuple(
                bind_device(logical_id=name, device=device, physical_id=f"bench:{device.channel}")
                for name, device in self.devices.items()
            )
        )

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
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
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")


def report(label: str, error: DiagnosticError) -> None:
    diagnostic = error.diagnostics[0]
    attached = " (source attached)" if diagnostic.source is not None else ""
    print(f"{label}: {type(error).__name__} [{diagnostic.code}]{attached}")
    print(f"    {diagnostic.message}")


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

# One authored program, two deployments, two different rejections.
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

for label, profile in (("a writable heater", BenchHeater()), ("a read-only heater", FixedHeater())):
    selected = Adaptive().compile(target=BenchTarget(devices={"heater": profile})).specialized_ir
    print(f"adaptive on {label}:", ", ".join(type(node).__name__ for node in selected.functions[0].body))
```
