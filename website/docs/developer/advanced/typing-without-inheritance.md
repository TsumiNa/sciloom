# Typing without inheritance

`Target` is a structural protocol. You do not import it and you do not subclass
it; your class matches it by having the four members, and `target_id` may be a
plain class attribute or a property.

The runtime check in `compile_ir` only verifies that the four members exist, so
passing a string or a half-written object gives a readable `TypeError` instead
of an obscure one. Argument and return types are a static contract: run
`uv run mypy` over your package to check them, and annotate a variable as
`Target` if you want the checker to compare your class against the protocol.

## What mypy sees

`Input`, `Output` and `Var` are `Annotated` aliases. Mypy sees the Python value
type, while SciLoom reads the role metadata. Wrong scalar and list assignments
and invalid device property types are caught statically. The `runtime` and
`operation` decorators preserve signatures, and `comptime.is_device` is a
`TypeGuard`, so inside its branch the slot has the narrowed type and
`self.heater.gain` type-checks.

## What mypy does not enforce

Host-time field protection, role nesting, mandatory `Var` initializers, every
Function call binding, the source subset and vendor constraints are all outside
the type checker. Python's `bool`/`int` subtype relationship also differs from
SciLoom's index rules. Schema, IR and target validation remain necessary, which
is why the [rejection layers](../reference/pipeline.md#who-can-say-no) exist.
