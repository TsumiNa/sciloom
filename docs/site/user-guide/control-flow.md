# Runtime control flow

Inside `@runtime`, write ordinary assignments, `if/elif/else` and `while` statements.
SciLoom deliberately accepts a restricted source language rather than arbitrary
Python. Unsupported constructs produce diagnostics pointing to their source.

Supported expressions include scalar/list literals, registered `self` fields,
host scalar configuration, arithmetic `+ - * /`, unary signs, individual comparisons,
Boolean `not`, and list length/indexing. Division produces float. If and While
conditions must be Boolean.

Assignment and augmented assignment are supported. Function calls are statements:
bind their outputs directly rather than nesting calls inside arithmetic.
`pass` and string/docstring statements have no execution effect.

Python local temporaries, arbitrary helper calls, module-global value lookups,
chained comparisons, `for`, `break`, `continue`, loop `else`, `return`, exception
handlers and arbitrary attribute chains are not implemented. Runtime state must
be declared on the class. Device properties have their own restricted write-only
contract described in [Devices](devices.md).

## Target restrictions

The semantic model and reference interpreter support short-circuit `and`/`or`.
The AutoSuite target currently rejects them because equivalent target behavior
has not been established. Use nested `if` statements for AutoSuite, as in the
[minimum example](../examples/non-zero-array-min.md). AutoSuite also rejects
recursive calls even though the semantic model can represent them.

Device-dependent compilation uses the separate [compile-time queries](devices.md#device-dependent-branches).
Their arguments cannot depend on runtime values.
