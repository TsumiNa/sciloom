# Author API

Import experiment-author interfaces from `sciloom`. See also [units](units.md),
[device queries](comptime.md) and the [AutoSuite contribution](autosuite.md).

::: sciloom.Function
    options:
      members: [compile, to_ir]

::: sciloom.runtime

::: sciloom.log

::: sciloom.notify

::: sciloom.now_text

## Field declarations

`Input[T]`, `Output[T]` and `Var[T]` mark runtime fields while keeping their Python
value type visible to type checkers. A Var needs an explicit initial value.
Unwrapped value annotations remain host-time data. Runtime fields cannot be read
or written as ordinary values by host Python.

::: sciloom.Input

::: sciloom.Output

::: sciloom.Var

::: sciloom.Agitator
    options:
      members: [speed, start, stop]
