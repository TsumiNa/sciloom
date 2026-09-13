# Add a target

A target is the only component that knows a platform. Everything above it works on
semantic IR, so a target is where a program becomes an AutoSuite file, a JSON
recording, or whatever your instrument reads.

A target is not a subclass and not a plugin. It is four members the compiler calls
by name, so a target written in your own package, importing nothing but SciLoom's
public contracts, works exactly like the shipped one. The shipped AutoSuite target
is itself a separate package, the workspace member `sciloom-autosuite`, so the
shape you build here is the shape it has.

This page continues the heater from [add a device](add-a-device.md).

## What the compiler asks of you

| Member | The compiler calls it to |
| --- | --- |
| `target_id` | Label the compile result, so a caller knows which platform produced it |
| `resolve_devices(program)` | Turn your deployment configuration into trusted binding facts |
| `validate(program)` | Collect the reasons your platform cannot run this program |
| `emit(program)` | Produce the artifact bytes |

## Step 1: validate deployment configuration when the target is built

A target carries deployment data: which physical instrument stands behind each
logical name. Check it in `__init__`, not later.

```python
    def __init__(self, *, devices: Mapping[str, BenchHeater]) -> None:
        if any(type(device) is not BenchHeater for device in devices.values()):
            raise TypeError("BenchTarget requires BenchHeater deployment profiles.")
        if any(not device.channel for device in devices.values()):
            raise ValueError("Bench channels must not be empty.")
        self.devices = MappingProxyType(dict(devices))
```

An author who hands you the wrong profile finds out when they build the target,
with an ordinary Python error at the line that built it. Deferring that to
compilation would turn a typo into a diagnostic about a program that is fine.

## Step 2: resolve devices into trusted facts

```python
    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings(
            devices=tuple(
                bind_device(logical_id=name, device=device, physical_id=f"bench:{device.channel}")
                for name, device in self.devices.items()
            )
        )
```

`bind_device` reads a profile's declarations and returns what the compiler trusts:
the logical name the program used, the physical identity you chose, the profile's
contract and every ancestor contract.

You are answering a question, not making a decision: the program already said which
logical devices it needs. Bind every one of them. An empty envelope is valid only
for a program with no devices. What you return is then checked for you, so a
profile that cannot write a property the program writes is rejected before your
`validate` ever runs.

This is also the one place that sees the **authored** program, before device
branches are selected. Validation and emission see the selected program.

## Step 3: reject what your platform cannot do, and only what you can prove

`validate` returns diagnostics; it does not raise. The compiler collects them and
raises once, so an author sees every problem in a program rather than the first.

```python
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
```

The rule this encodes matters more than the code. A hold of `30.0` is a literal, so
the platform limit is provable and the program compiles. A hold of `self.seconds` is
a runtime input, and this target cannot prove anything about it, so it rejects:

```text
rejected: [bench_hold_limit] $.functions[0].body[1]
message: hold() requires a literal duration; this target proves literals only.
source attached: True
```

A literal of `900.0` reaches the second branch instead and is rejected for its
value: `hold() must be within [0, 600.0] s on this bench.` Each branch writes its
own message, because "this target proves literals only" explains nothing about a
literal that is simply too large.

One subtlety is worth seeing early, because it decides how conservative a target
must be. `hold(-1.0)` is not a literal in the IR: Python parses it as a negation of
`1.0`, and it lowers to a `Unary` node. This target therefore refuses it as
unprovable rather than by range. That is the correct outcome here, and it is a good
illustration of why a target should inspect the IR it actually receives rather than
the source it imagines.

Rejecting the unprovable is honest; accepting it and hoping is not.
[Reject a program](reject-a-program.md) covers every layer that can say no, and when
to let a program adapt instead. A target that
could evaluate ranges would accept more, and the message says which kind of target
this is so the author knows what to change.

Fill in every field of the diagnostic. `code` is yours and should be specific
enough to search for. `path` and `node_id` come from the traversal. `source` is the
author's own Python line, carried from lowering, so a rejection from deep inside
your platform rules still points at the statement the author wrote.

## Step 4: emit bytes, not a connection

```python
    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")
```

An artifact is bytes with a media type and a filename suffix. It is not a string, a
file path, or an open connection to an instrument. Compilation stays a pure
function of the program and your deployment data, which is what makes it testable
and repeatable. `CompileResult.write(path)` puts those bytes on disk when someone
asks for a file.

## Where your target sits

The complete example prints the order the compiler used:

```text
pipeline: resolve_devices -> validate -> emit
```

Between your first and second call the compiler validates the program's structure
and types, selects device branches against your bindings, checks that every bound
profile supports what the program does with it, and checks that a lifecycle start
has its required configuration on every reachable path. Your `validate` is the last
gate before bytes, and it is the only one that knows your platform.

## Typing, without inheritance

`Target` is a structural protocol. You do not import it and you do not subclass it;
your class matches it by having the four members. `target_id` may be a plain class
attribute or a property.

The runtime check in `compile_ir` only verifies the four members exist, so passing a
string or a half-written object gives a readable `TypeError` instead of an obscure
one. Argument and return types are a static contract: run `uv run mypy` over your
package to check them, and annotate `Target` explicitly if you want the checker to
compare your class against it.

## The complete example

```python
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from sciloom import Function, Input, Output, runtime
from sciloom.core.compiler import Artifact
from sciloom.core.devices import DeviceBindings
from sciloom.core.diagnostics import CompilationError, Diagnostic
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
    """A concrete deployment of the heater family."""

    channel: str = "A"
    device_type_id: ClassVar[str] = "example.bench-heater/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ("setpoint",)
    required_configuration: ClassVar[tuple[str, ...]] = ("setpoint",)
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (Heater.hold,)


class BenchTarget:
    """Record the selected program as JSON, within one bench's proven limits."""

    target_id = "example.bench/v1"
    max_hold_seconds = 600.0

    def __init__(self, *, devices: Mapping[str, BenchHeater]) -> None:
        if any(type(device) is not BenchHeater for device in devices.values()):
            raise TypeError("BenchTarget requires BenchHeater deployment profiles.")
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


class ShortHold(Function):
    """Hold a caller-selected temperature for a fixed, provable duration.

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


target = BenchTarget(devices={"heater": BenchHeater(channel="A")})
result = ShortHold().compile(target=target)
print("pipeline:", " -> ".join(target.calls))
print("artifact:", result.artifact.media_type)
assert target.calls == ["resolve_devices", "validate", "emit"]
assert result.target_id == "example.bench/v1"

try:
    RuntimeHold().compile(target=BenchTarget(devices={"heater": BenchHeater(channel="A")}))
    raise AssertionError("an unprovable hold duration should be rejected")
except CompilationError as error:
    diagnostic = error.diagnostics[0]
    assert diagnostic.code == "bench_hold_limit"
    print(f"rejected: [{diagnostic.code}] {diagnostic.path}")
    print("message:", diagnostic.message)
    print("source attached:", diagnostic.source is not None)

try:
    BenchTarget(devices={"heater": BenchHeater(channel="")})
    raise AssertionError("an empty channel should be rejected when the target is built")
except ValueError as error:
    print("deployment:", error)
```
