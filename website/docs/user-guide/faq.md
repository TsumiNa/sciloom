# FAQ

**Why can't I write a `for` loop?** The runtime language has `while` only.
Declare an index as a `Var`, reset it at the top of the method, and loop while
it is below `len(...)`. See [lesson 4](tutorial/lists-and-loops.md).

**Why is there no `return`?** A Function hands results back through `Output`
fields, which must be assigned on every path through the method. See
[lesson 3](tutorial/agitator.md).

**Can I use a local variable inside `@runtime`?** No. Every name the method
assigns is a declared field; use a `Var`. See the
[runtime language](reference/runtime-language.md).

**Does a `Var` reset on every call?** No. Its literal is the state when the
session starts, and later calls continue from where the last one stopped. Reset
it inside the method when a call should start fresh. See
[lesson 5](tutorial/compile.md).

**Can an `Input` have a default value?** No; `Input` and `Output` have no
defaults. Pass the value from the caller, or store it in the constructor as host
configuration. See [host-time specialization](advanced/specialization.md).

**Why is `speed = 0 * rpm` not a stop?** Assigning a property saves a
configuration; only `stop()` disables the device. See
[lesson 2](tutorial/inputs-and-units.md).

**Can I read the shaker's current speed?** No. Device properties are write-only
in this release; keep the value you configured in a `Var`. See
[devices and targets](reference/devices-and-targets.md).

**Why does AutoSuite refuse `and` / `or`?** Equivalent short-circuit behaviour on
the platform has not been established, so the target rejects them. Nest two
`if` statements instead. See [AutoSuite rules](advanced/autosuite.md).

**I declared a device slot I no longer use; why must I still bind it?** A slot
is a declared resource of the program, whether or not the method touches it.
Remove the declaration or bind it. See [AutoSuite rules](advanced/autosuite.md).

**Why must a list output be assigned as a whole before my loop?** AutoSuite
needs the output to exist on every path, including the path on which the loop
runs zero times. Start with `self.result = self.values` or `self.result = []`.
See [AutoSuite rules](advanced/autosuite.md).

**Can I run my experiment without hardware?** Not from the author API.
Compilation checks and produces a package; it does not execute it. The
reference interpreter is a developer tool that defines SciLoom semantics, and
it proves nothing about equipment. See
[what compilation establishes](../introduction/status.md#what-compilation-establishes).

**Which AutoSuite versions are supported?** `AutoSuiteVersion.V2_47_1_1` only,
which is the default. See [AutoSuite rules](advanced/autosuite.md).

**Can I define a Function in a notebook or the REPL?** No. SciLoom reads the
method's source from an ordinary `.py` file. See
[declarations](reference/declarations.md).

**How do two Functions share one shaker?** Assign the parent's slot to the
child's slot in the constructor: `self.stage.shaker = self.shaker`. See
[composition](advanced/composition.md).

**How do I write one program for two instruments?** Ask the compiler with a
compile-time query, `comptime.is_device`, `can_write` or `supports`, and put the
instrument-specific statements in that branch. See
[device-dependent branches](advanced/device-branches.md).

**Do docstrings change what compiles?** No. They describe the procedure and its
fields for readers and tools. See [declarations](reference/declarations.md).

**Where is a diagnostic code explained?** On [troubleshooting](troubleshooting.md),
grouped by when the error fires, with the fix beside each code.
