# 5. Reject a program

A program can be wrong in many ways, and SciLoom answers at the earliest layer
that can prove it wrong. Knowing which layer speaks tells you where your own
check belongs, and why some mistakes are caught while you are still typing the
class and others only once a target is chosen. The
[compilation pipeline](../reference/pipeline.md#who-can-say-no) lists the eight
layers; this page provokes five of them.

<!-- tutorial: step -->
```python
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
```

<!-- tutorial: checkpoint -->
```text
declaration: IRValidationError [class_schema]
    Device slot 'heater' cannot have a class-level value.
source: IRValidationError [device_property_read] (source attached)
    Device getters are not supported; use a runtime variable for the configured value.
capability: CompilationError [device_capability] (source attached)
    The bound device does not implement this writable property contract.
platform: CompilationError [bench_hold_limit] (source attached)
    hold() requires a literal duration; this target proves literals only.
deployment: Bench channels must not be empty.
```

Each layer only knows what it can see. The class body has no target, so it
cannot know your heater is read-only. The target has no Python source, so it
cannot know which variable the author called `seconds`, only that the argument
is not a literal. That is why a diagnostic carries a source span: the layer that
proves the problem is rarely the layer the author was thinking about.

The same authored program produced the capability and platform rejections:
`RuntimeHold`, compiled once against a fixed heater and once against a writable
one. Nothing about the program changed; the deployment did. This is the point of
compiling against explicit bindings rather than against an assumed instrument.
The deployment error is different in kind: it is an ordinary `ValueError` from
the target's constructor, raised before any program exists.

## Reading a diagnostic

Every rejection carries the same record.

| Field | Use |
| --- | --- |
| `code` | The rule that fired, stable enough to search for or match in a test |
| `message` | What is wrong, in the author's vocabulary |
| `path` | Where in the program, as a semantic path such as `$.functions[0].body[1]` |
| `node_id` | The exact node, for tooling that maps back to a graph |
| `source` | The author's Python file and line, when the program came from source |

The aggregating layers carry **all** the diagnostics they found, not the first,
so an author can fix a batch rather than recompile once per mistake. IR
validation, the binding and configuration checks and `Target.validate` all
collect. Declaration and source analysis raise at the first problem, because a
half-built class or an unparsable method makes everything after it meaningless.

## Where your own check belongs

Ask what the check actually knows about.

**A declaration.** Nothing to add: declaring a capability list wrong, naming a
slot after a host member, or omitting a versioned identity is already rejected
when the class body runs. Your job is to declare honestly.

**Your deployment data.** Check it in the target's `__init__` and raise an
ordinary `TypeError` or `ValueError`. The author is holding the wrong profile,
and they find out at the line that built the target.

**The program on your platform.** That is `Target.validate`. Return diagnostics,
one per rule, with your own code. Reject only what you can prove, and say in the
message what would be accepted.

**Something the program should survive.** Do not reject at all: let the program
adapt, as the next page shows.

## Writing a rejection the author can act on

The platform diagnostic above says three things in one line: the rule (`hold()`
has a limit), the reason it fired (the argument is not a literal), and what this
target is capable of proving (literals only). An author can act on it without
reading your source. Compare `invalid hold`, which says only that you are
unhappy.

Give each rule its own `code` and keep the code stable. `path` is required; take
it from the traversal. `node_id` and `source` are optional, so attach them from
the node you rejected whenever it has them. Programmatically built IR may carry
no source at all, which is exactly why a message has to stand on its own. A
target that returns a single `Diagnostic(code="error", message="cannot compile",
path="$")` is technically valid and practically useless.

Next: [6. Adapt with comptime](adapt-with-comptime.md).
