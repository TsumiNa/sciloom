# FAQ

**Do I change SciLoom to add my instrument?** No. A family, its profiles and a
target all live in your own package and import only public contracts; the
shipped AutoSuite target is itself a separate package. See
[the heater story](tutorial/index.md).

**Family or profile?** A profile describes one concrete instrument of a family
SciLoom already knows and is [step 2](tutorial/declare-profiles.md) alone. A
family teaches SciLoom a new kind of instrument and is the whole series.

**Why does the Function name `Heater` rather than `BenchHeater`?** So the
program, and its JSON, can be bound to any heater profile later without
recompiling from Python. See [write a Function](tutorial/write-a-function.md)
and [JSON interchange](advanced/json-interchange.md).

**Why are capability lists not inherited?** A profile promises what its hardware
does; a promise inherited by accident is not a promise. `bind_device` refuses a
profile that omits a list. See [device contracts](reference/device-contracts.md#profiles).

**Why is my family's `required_configuration` not enforced?** The compiler
enforces definite configuration only where a `StartAgitation` node requires it;
a generic `DeviceCommand` neither requires nor supplies configuration. Enforce
it in your target's `validate`. See
[required configuration](reference/device-contracts.md#required-configuration).

**Why can't the interpreter run my command?** A native command has meaning only
on its hardware; the interpreter refuses to invent one. See
[native commands](advanced/native-commands.md).

**Reject or adapt?** Reject what your platform cannot do and can prove; let a
program adapt with a compile-time query when it is genuinely correct on both
instruments. See [reject a program](tutorial/reject-a-program.md) and
[adapt with comptime](tutorial/adapt-with-comptime.md).

**Why does `resolve_devices` see a different program than `validate`?** Resolution
sees the authored program, before device branches are selected; validation and
emission see the selected one. See the
[compilation pipeline](reference/pipeline.md#steps).

**May a target import `sciloom.flow` or `sciloom.dsl`?** No. A target imports
`sciloom.core` for the contracts and `sciloom.devices` to declare and bind
hardware, never the authoring vocabulary or the source analysis. See
[architecture](reference/architecture.md#layering).

**Does compiling prove the program runs on hardware?** No. Compilation and
reference execution check structure and mapped semantics; the platform's own
validation and physical tests remain. See
[verification](reference/verification.md).

**Which minimal target should I copy?** `SummaryTarget` on the
[Target contract](reference/target-contract.md) page is the smallest legal
target; the tutorial's `BenchTarget` adds deployment data and a platform rule.
Start from whichever matches your instrument.
