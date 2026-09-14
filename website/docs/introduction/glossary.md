# Glossary

One definition per term, with the page that explains it. Authoring terms are
what an experiment author meets; contributor terms belong to people who extend
SciLoom with devices and targets.

## Authoring terms

**Function.** A Python class whose body declares a procedure's fields and whose
one `@runtime` method holds its steps; SciLoom compiles it rather than running
it. [Tutorial 1](../user-guide/tutorial/first-function.md).

**Runtime method.** The single method marked `@runtime`, taking only `self`,
whose source SciLoom reads. [Declarations](../user-guide/reference/declarations.md).

**Host time and runtime.** Host time is when your Python runs: constructing
instances, storing configuration, compiling. Runtime is when the compiled
program executes on equipment. [Host-time specialization](../user-guide/advanced/specialization.md).

**Input, Output, Var.** The three field roles: a value supplied at each call, a
value written back at each call, and persistent state of the instance.
[Tutorial 2](../user-guide/tutorial/inputs-and-units.md).

**Host configuration.** An attribute stored in `__init__` or an unwrapped class
annotation; a scalar one becomes a literal in the program. [Host-time specialization](../user-guide/advanced/specialization.md).

**Child Function.** A Function instance stored on a parent in `__init__` and
called from the parent's runtime method. [Composition](../user-guide/advanced/composition.md).

**Logical device, device slot.** A field declared with a device family type,
`shaker: Agitator`: the program's need for an instrument, not the instrument.
[Tutorial 4](../user-guide/tutorial/agitator.md).

**Profile.** Deployment data for one concrete instrument, such as
`AutoSuiteIndividualShaker(zone=..., device_id=...)`, that a target binds to a
slot. [Tutorial 5](../user-guide/tutorial/compile.md).

**Binding.** The mapping from a slot's name, a field name or a component path
such as `stage.shaker`, to a profile. [Devices and targets](../user-guide/reference/devices-and-targets.md).

**Target.** The equipment platform a program is compiled for, chosen
explicitly: `AutoSuiteTarget`. [AutoSuite rules](../user-guide/advanced/autosuite.md).

**Artifact.** What a target produces: for AutoSuite, an `.asfp` package.
[Tutorial 5](../user-guide/tutorial/compile.md).

**Compile-time query.** `comptime.is_device`, `can_write` or `supports`, asked
as the whole condition of an `if`; the compiler keeps the branch that applies to
the bound device. [Device-dependent branches](../user-guide/advanced/device-branches.md).

**Specialization.** Fixing a program to one deployment: host values become
literals, and device-dependent branches are selected. [Host-time specialization](../user-guide/advanced/specialization.md).

**Definite configuration.** The proof, made by the compiler, that every
property a `start()` requires was assigned on every path that reaches it.
[Tutorial 4](../user-guide/tutorial/agitator.md).

**Diagnostic.** A structured error: code, message, path into the program and,
when known, the source line. [Troubleshooting](../user-guide/troubleshooting.md).

**Rotational speed, rpm, rps.** The one physical quantity in this release,
written as a number times a unit; revolutions per second is canonical.
[Tutorial 2](../user-guide/tutorial/inputs-and-units.md).

**Whole-list assignment.** Assigning a complete list to a list output before
any element is read or written, which AutoSuite requires on every path.
[AutoSuite rules](../user-guide/advanced/autosuite.md).

**Zone, device id.** The two facts an AutoSuite shaker profile carries: the
instrument's zone name and its positive decimal id. [AutoSuite rules](../user-guide/advanced/autosuite.md).

**AutoSuite Executor.** The vendor's validator on the deployment host, which
compilation does not replace. [What compilation establishes](status.md#what-compilation-establishes).

**Reference execution.** Running a program with SciLoom's own interpreter to
define its semantics; a developer tool that proves nothing about equipment.
[Reference execution](../developer/reference/interpreter.md).

## Contributor terms

**Family.** A subclass of `BaseDevice` declaring what any instrument of its kind
can be asked to do; never a specific instrument. [Declare a family](../developer/tutorial/declare-a-family.md).

**Profile.** A concrete subclass of a family carrying immutable deployment data
and the three capability lists. [Declare profiles](../developer/tutorial/declare-profiles.md).

**Slot.** A Function field typed with a family; the program's declared need for
an instrument. [Write a Function](../developer/tutorial/write-a-function.md).

**Contract.** The data form of a declaration: a `DeviceTypeContract` with its
ancestors, properties, commands and required configuration, read statically. [Device contracts](../developer/reference/device-contracts.md).

**Binding.** A `DeviceBinding`: the trusted facts a target answers for one
resource, built by `bind_device`. [Target contract](../developer/reference/target-contract.md#bindings).

**Target.** Four members the compiler calls by name: `target_id`,
`resolve_devices`, `validate`, `emit`. [Target contract](../developer/reference/target-contract.md).

**Artifact.** Bytes with a media type and a suffix; what `emit` returns. [Target contract](../developer/reference/target-contract.md#members).

**Authored and selected program.** The program as written, with every device
branch, versus the program after specialization for one deployment. [Compilation pipeline](../developer/reference/pipeline.md#steps).

**Specialization.** The pure function that answers device-dependent branches
from bindings and retypes resources to their profiles. [Specialization internals](../developer/advanced/specialization.md).

**Definite configuration.** The compiler's proof that every property a lifecycle
start requires was written on every reachable path. [Required configuration](../developer/reference/device-contracts.md#required-configuration).

**Semantic id.** The namespaced, versioned identifier of a device type, property
or command, carried into JSON. [Device contracts](../developer/reference/device-contracts.md#identity).

**Diagnostic.** Code, message, path, node id and source span; what every
rejection carries. [Reject a program](../developer/tutorial/reject-a-program.md#reading-a-diagnostic).

**Native command.** A `DeviceCommand`: a command with a semantic id and typed
arguments, emitted by targets and refused by the interpreter. [Native commands](../developer/advanced/native-commands.md).

**Reference execution.** Running a selected program with SciLoom's interpreter
to define its semantics. [Reference execution](../developer/reference/interpreter.md).
