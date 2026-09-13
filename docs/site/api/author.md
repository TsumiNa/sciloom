# Author API

Import experiment-author interfaces from `sciloom`. This initial reference covers
the source model, field declarations and logical agitator; the complete contributor
catalogue is added separately.

::: sciloom.Function
    options:
      members: [compile, to_ir]

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
