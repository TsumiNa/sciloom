# FAQ

## How do I change the stirring speed?

For a fixed speed, change `300 * rpm` in the source and compile again
([lesson 1](tutorial/first-function.md)). To choose a speed each time the
generated function is called, declare `speed: Input[RotationalSpeed]` and use
`self.shaker.speed = self.speed` ([lesson 2](tutorial/inputs-and-units.md)).
The caller supplies that input when the function runs.

## How do two steps use the same shaker?

Create the child in `__init__`, then share the logical reference with
`self.stage.shaker = self.shaker`. Bind the parent's `"shaker"` once in
the target. See the complete [shared shaker example](advanced/composition.md).
A concrete `AutoSuiteIndividualShaker` belongs in the target's `devices`
dictionary, not in either Function's fields.

## Why does my counter keep increasing?

A `Var` keeps its value between calls using the same runtime state. Its
class-level initial value is used when that state is created. To start each
call at zero, assign `self.count = 0` at the beginning of `run`.
[Lesson 5](tutorial/compile.md) compares a persistent counter with a loop index
that resets on every call.

## Why did assigning a new speed not change the running shaker?

Assignment saves the next configuration. Call `start()` to apply it, even
if the shaker is already running. Use `stop()` to stop; assigning
`0 * rpm` alone does not stop it.
See [device operations](reference/devices-and-targets.md#agitator).

## Can I read the shaker's current speed?

Measured speed is not available through this API. Device properties currently
allow writes only. If the procedure needs to reuse the speed it requested,
keep that value in a `Var[RotationalSpeed]`. That value is a requested
setting, not a measurement.

## Can an input have a default? Must I supply it when stopping?

Inputs have no defaults, and the caller must supply every input on every call,
including inputs a particular branch does not use. The start/stop example needs
both `enabled` and `speed` when stopping.
If a setting should be fixed in the generated program, use
[a constructor parameter](advanced/specialization.md) instead of an input.

## How do I return a calculation's result?

Declare an `Output[T]` and assign it on each path through `run`. A parent
receives it with `self.result = self.child(...)`; do not write `return`
in the runtime method. [Lesson 3](tutorial/agitator.md) shows a speed calculation.

## Can I use a temporary variable or a for loop?

Declare working values as `Var` fields and refer to them through `self`.
Use a `while` loop with an index for a list. For sample locations, use
`for self.well in self.rack` with a declared `Var[Zone]` target; see
[sample locations](reference/zones.md). General Python iteration and local
runtime variables remain unsupported. Ordinary Python outside `@runtime` can
use both.
See [lesson 4](tutorial/lists-and-loops.md) and the
[runtime syntax reference](reference/runtime-language.md).

## Will changing a child's input list change the parent's list?

No. The child receives a copy. Whole-list assignment and output return also
copy values. In the [scaling example](../examples/scale-values.md), changing
`result[0]` leaves the supplied `values[0]` unchanged.

## Why must I assign an output list before updating its elements?

The elements must already exist. Use `self.result = self.values` to copy
an input, then update that copy. `self.result = []` creates an empty
result; it does not allocate space for indexed writes.
AutoSuite also requires a whole-list assignment on every return path, including
one where a loop runs zero times. See [AutoSuite restrictions](advanced/autosuite.md#current-autosuite-restrictions).

## Why does AutoSuite reject and / or?

Their Python short-circuit behaviour has not been established for this target.
Use nested `if` statements. This is an AutoSuite restriction; see
[the correction](troubleshooting.md#autosuite-rejects-boolean-combinations).

## Can the same procedure work with another instrument?

It can if a target supports the required device operations. Use
[device-dependent branches](advanced/device-branches.md) for differences between
profiles. These queries use the target's declared capabilities at compilation;
they do not inspect connected hardware.

## I no longer use a declared shaker. Do I still need to bind it?

Yes. Remove its declaration, or provide a binding. A declared slot remains a
device dependency even when no runtime statement uses it.

## Can I run or validate a procedure without equipment?

You can generate an ASFP without a connected instrument. SciLoom also has a
[reference interpreter](../developer/reference/interpreter.md) for developers
to check calculations and state changes. It does not simulate the instrument.
Generated packages still need AutoSuite Executor validation before equipment
use; see [validation limits](../introduction/status.md#what-compilation-establishes).

## Which Python and AutoSuite versions can I use?

Python 3.12–3.14 and AutoSuite serialization version
`AutoSuiteVersion.V2_47_1_1`, the default. Follow
[Getting started](../introduction/getting-started.md) to install the checkout.
Keep Functions in ordinary `.py` files; notebook, REPL and `exec()` definitions
are not supported.

## Do docstrings affect the experiment?

No. They explain the procedure and its fields to readers and tools. Declarations
and runtime statements determine what compiles.
See [declarations](reference/declarations.md#docstrings).

## Where can I look up an error?

[Troubleshooting](troubleshooting.md) groups errors by the problem you see,
with diagnostic codes and corrections.
