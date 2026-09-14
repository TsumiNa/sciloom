# AutoSuite rules

`AutoSuiteTarget` compiles a program into an `.asfp` package. Beyond the checks
every target performs, it applies rules of its own, and it refuses what it cannot
express rather than approximating.

```python
from sciloom import Agitator, Function, Input, Output, RotationalSpeed, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget, AutoSuiteVersion


class TwoShakers(Function):
    """Start two shakers at one speed.

    Attributes:
        left: First logical agitator.
        right: Second logical agitator.
        speed: Speed for both.
    """

    left: Agitator
    right: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.left.speed = self.speed
        self.right.speed = self.speed
        self.left.start()
        self.right.start()


target = AutoSuiteTarget(
    version=AutoSuiteVersion.V2_47_1_1,
    devices={
        "left": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
        "right": AutoSuiteIndividualShaker(zone="Heater Shaker 24", device_id="24"),
    },
)
print(TwoShakers().compile(target=target).artifact.media_type)


class Both(Function):
    """A condition AutoSuite refuses.

    Attributes:
        a: First flag.
        b: Second flag.
        both: Whether both flags are set.
    """

    a: Input[bool]
    b: Input[bool]
    both: Output[bool]

    @runtime
    def run(self) -> None:
        self.both = self.a and self.b


try:
    Both().compile(target=AutoSuiteTarget())
except Exception as error:
    print(error)
```
```text
application/xml
$.functions[0].body[0].value: AutoSuite short-circuit equivalence is unverified; lower to explicit If statements. [unsupported_short_circuit]
```

## Version and artifact

`AutoSuiteVersion.V2_47_1_1` is the only supported version and the default. The
artifact is UTF-8 XML with media type `application/xml` and suffix `.asfp`;
`write` adds no suffix of its own. The package contains a callable procedure
whose runtime inputs are supplied when AutoSuite runs it. The adapter keeps saved
device configuration in its own storage and isolates list parameters so that
lists keep value semantics; none of this changes the program's input and output
signature.

--8<-- "website/snippets/hardware-boundary.md"

## Binding shakers

`devices` maps each declared slot, by field name or component path, to an
`AutoSuiteIndividualShaker(zone=..., device_id=...)`. The profile is deployment
data: the zone is the instrument's AutoSuite zone name and the id is the
individual shaker's positive decimal id. Two slots cannot share a device id or a
zone. Every declared slot needs an entry, including one the runtime method never
uses, and an entry without a declared slot is an error. A program with no device
compiles with `AutoSuiteTarget()`.

## What AutoSuite refuses

| Rule | Code | Write instead |
|---|---|---|
| `and` / `or` in any expression | `unsupported_short_circuit` | nested `if` statements, as in the [minimum example](../../examples/non-zero-array-min.md) |
| a Function that calls itself, directly or through another | `recursive_call` | a `while` loop |
| a list output read or updated before it was assigned as a whole list on every path | `list_output_initialization` | `self.result = self.values` or `self.result = []` first, before any loop that may run zero times |
| a statement the package format has no form for | `unsupported_operation` | a supported operation |

The semantic model and the reference interpreter accept short-circuit operators
and recursion; only this target rejects them, because equivalent behaviour on
the platform has not been established.
