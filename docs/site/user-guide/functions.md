# Functions and fields

A Function is a reusable experimental procedure expressed in Python. Define its
runtime schema at class level; create an instance to specialize and compose it.

| Declaration | Meaning | Default |
|---|---|---|
| `value: Input[float]` | Value supplied by the caller | Not supported |
| `result: Output[float]` | Value written back after return | Not supported |
| `index: Var[int] = 0` | Internal runtime state | Required |
| `batch_size: int = 8` | Ordinary host-time configuration | Ordinary Python |
| `agitator: Agitator` | Logical device dependency | Target binds hardware |

Import Function, Input, Output, Var and runtime from `sciloom`. Use exactly one
field role: bare aliases and nested roles are errors. Inherited runtime fields
and methods work, but redeclaring inherited runtime fields is outside the current
subset. Constructor assignments do not silently create runtime fields.

## Host time and runtime

`__init__` is ordinary Python: store configuration and child Function instances
there. An unwrapped numeric annotation is host data, not runtime state. Host scalar
values referenced through `self` can be embedded during source conversion.

Each Function has one synchronous `@runtime` instance method taking only `self`.
SciLoom reads its source; calling that method directly from host Python raises an
error. Runtime field values are also protected against host-time reads and writes.
Keep the original `.py` source available during compilation. Notebook cells,
interactive definitions, `exec()` and asynchronous methods are unsupported.

## State and repeated calls

A Var initializer establishes initial state, not an assignment on every call.
Reset a counter explicitly inside the runtime method when each call should start
at zero. State is owned by a Function instance; different instances have distinct
state. [Composition](composition.md) explains sharing a child instance.

Inputs and outputs are exchanged at each invocation. Assign outputs before they
are read and on every normal return path. List defaults are copied and frozen
when the class schema is built, so later mutation of an initializer cannot alter
the declared program.

## Describe the experiment

Use an English class docstring explaining the procedure and an `Attributes`
section whose names match the declared fields. Describe constructor configuration
in `Args`. Types come from annotations. Docstrings help people, AI and future
editor tooling understand intent; they do not change execution rules.

See [function calls](../examples/function-call.md) and
[list scaling](../examples/scale-values.md) for complete source files.
