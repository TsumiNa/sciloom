# 4. Write a target

A target is the only component that knows a platform. Everything above it works
on semantic IR, so a target is where a program becomes an AutoSuite file, a JSON
recording, or whatever your instrument reads. It is four members the compiler
calls by name, so a target written in your own package, importing nothing but
SciLoom's public contracts, works exactly like the shipped one; the shipped
AutoSuite target is itself a separate package, the workspace member
`sciloom-autosuite`.

<!-- tutorial: step -->
```python
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
```

<!-- tutorial: checkpoint -->
```text
pipeline: resolve_devices -> validate -> emit
target: example.bench/v1 artifact: application/json
selected contracts: ['example.bench-heater/v1', 'example.heater/v1', 'sciloom.device/v1']
```

## Check deployment data when the target is built

A target carries deployment data: which physical instrument stands behind each
logical name. Check it in `__init__`, not later. An author who hands you the
wrong profile finds out when they build the target, with an ordinary Python error
at the line that built it. Deferring that to compilation would turn a typo into a
diagnostic about a program that is fine.

## Resolve devices

`bind_device` reads a profile's declarations and returns what the compiler
trusts: the logical name the program used, the physical identity you chose, the
profile's contract and every ancestor contract. You are answering a question, not
making a decision: the program already said which logical devices it needs, so
bind every one of them. What you return is then checked for you, so a profile
that cannot write a property the program writes is rejected before your
`validate` ever runs. This is also the one place that sees the **authored**
program, before device branches are selected; validation and emission see the
selected program, whose contracts now name the profile, as the last printed line
shows.

## Reject only what you can prove

`validate` returns diagnostics; it does not raise. The compiler collects them and
raises once, so an author sees every problem in a program rather than the first.
A hold of `30.0` is a literal, so the platform limit is provable and the program
compiles. A hold of a runtime input cannot be proven by this target, so it
rejects; page 5 shows that rejection. A literal of `900.0` reaches the second
branch instead and is rejected for its value, with its own message, because
"this target proves literals only" explains nothing about a literal that is
simply too large.

One subtlety decides how conservative a target must be: `hold(-1.0)` is not a
literal in the IR. Python parses it as a negation of `1.0`, and it lowers to a
`Unary` node, so this target refuses it as unprovable rather than by range. That
is the correct outcome, and a good illustration of why a target inspects the IR
it actually receives rather than the source it imagines.

## Emit bytes, not a connection

An artifact is bytes with a media type and a filename suffix. It is not a
string, a file path, or an open connection to an instrument. Compilation stays a
pure function of the program and your deployment data, which is what makes it
testable and repeatable; `CompileResult.write(path)` puts the bytes on disk.

## Where your target sits

The printed pipeline is the order the compiler used. Between your first and
second call it runs the target-independent steps of the
[compilation pipeline](../reference/pipeline.md#steps); your `validate` is the
last gate before bytes, and it is the only one that knows your platform. The
member signatures and the binding rules are on the
[Target contract](../reference/target-contract.md).

`Target` is a structural protocol: your class matches it by having the four
members. [Typing without inheritance](../advanced/typing-without-inheritance.md)
explains what the type checker sees.

Next: [5. Reject a program](reject-a-program.md).
