# 2. Declare profiles

A profile is one deployable instrument: immutable data plus an explicit promise
about what it can actually do. Two profiles of the same family show why the
promise is explicit.

<!-- tutorial: step -->
```python
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
```

<!-- tutorial: checkpoint -->
```text
BenchHeater: writes ['example.heater.setpoint/v1'], runs ['example.heater.hold/v1']
FixedHeater: writes [], runs ['example.heater.hold/v1']
inherited lists: Concrete device profiles must explicitly declare writable_properties.
```

The three capability lists must be declared on the profile itself. Inheriting
them is rejected, deliberately: a profile promises what its hardware does, and a
promise inherited by accident is not a promise. `LazyHeater` shows the refusal.
A heater that cannot be set, only read back, declares an empty
`writable_properties`, and a program that writes to it fails to compile rather
than failing on the bench; page 5 shows that rejection.

Use `ClassVar` for all three. Without it a frozen dataclass would turn them into
instance fields. The frozen dataclass carries the deployment data, here a
`channel`; a target reads it when it binds.

`bind_device` is the target's tool, used here only to read back what each
profile promised: the semantic ids it accepts writes to and the commands it runs.
Page 4 uses it for real.

Adding a profile to an existing family is this page alone. The
[independent device example](../../examples/demo-device.md) is exactly that:
`DemoAgitator` adds one parameter and one native command to the shipped
`Agitator` family, with no change to SciLoom.

Next: [3. Write a Function against the family](write-a-function.md).
