# Values, units and lists

Runtime value types are `int`, `float`, `bool`, `RotationalSpeed`, and homogeneous
one-dimensional `list[T]` of these types. Input, Output and Var wrap the value type.
Python type checkers see the underlying type; SciLoom separately retains its role.

Boolean is distinct from integer. Integer values can widen to float, but float
cannot implicitly narrow to integer. Conditions must be Boolean; there is no
implicit numeric or list truthiness.

## Rotational speed

```python
from sciloom import RotationalSpeed, rpm, rps

speed = 600 * rpm
assert speed == 10 * rps
```

Use `Input[RotationalSpeed]` or `Var[RotationalSpeed]` for runtime speed values.
A bare number is not a rotational-speed quantity. Internally the canonical unit
is revolutions per second; the AutoSuite adapter encodes supported target units.
No general-purpose physical-units library or additional physical dimensions are
part of this release.

## Lists are values

Within a runtime method, given two list fields:

```python
self.b = self.a
self.b[0] = 9
```

The assignment copies the list value: `self.a` is unchanged by the element update.
Function input transfer and output writeback also avoid shared mutable aliases.
Different instances and execution sessions have independent initial lists.

Supported operations are empty/nonempty literals, whole-list assignment, Function
I/O, `len`, indexing, indexed assignment and indexed augmented assignment. Use
`while` and `if` to express algorithms. An empty literal needs a declared element
type. List variables require equal element types; a literal assigned to a typed
float list can widen integer elements.

Indices must be nonnegative integers; bool is not an index. Negative and out-of-
range access are execution errors. Writes do not extend the list. Bare `list`,
`list[Any]`, nested/heterogeneous lists, slicing, comprehensions, implicit iteration,
list comparisons/arithmetic, and append/pop/remove/clear are unsupported.

AutoSuite requires a whole-list output assignment before reading or updating it,
including paths on which a loop executes zero times. Start with
`self.result = self.values` or `self.result = []` as appropriate.

The [scaling example](../examples/scale-values.md) and
[minimum algorithm](../examples/non-zero-array-min.md) demonstrate these rules.
