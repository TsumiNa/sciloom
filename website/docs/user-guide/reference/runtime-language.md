# Runtime language

This reference applies inside `@runtime` methods. Constructors and the rest
of the Python script use ordinary Python.

## Values

| Type | Rules |
| --- | --- |
| `int`, `float` | Integers can widen to floats; floats do not narrow to integers |
| `bool` | Separate from integers; only Boolean expressions are valid conditions |
| `str` | Text without implicit numeric conversion or truthiness |
| `RotationalSpeed` | Nonnegative speed, such as `600 * rpm` or `10 * rps` |
| `Volume`, `Duration` | Signed, finite quantities, such as `2 * mL` or `1 * minute` |
| `list[T]` | One-dimensional list of a supported scalar or quantity type |

For a speed supplied by the caller, use `Input[RotationalSpeed]`.
The internal units are revolutions per second, cubic metres and seconds.

Lists require an element type: no bare `list`, `list[Any]`, mixed types
or nested lists. An empty `[]` gets its element type from its destination.
List-to-list assignment requires the same element type; a literal assigned to
`list[float]` may contain integers.

## Expressions

| Supported | Outside the source language |
| --- | --- |
| Literals, runtime fields, scalar host settings through `self` | Local variable names, arbitrary module globals or attribute chains |
| `+ - * /`, unary `+ - not` | `** % //`, bitwise operators |
| A single comparison: `== != < <= > >=` | Chained comparisons, `in`, `is` |
| `and`, `or` | Conditional expressions such as `a if flag else b` |
| List literals, indexing, `len(self.items)` | Slicing, comprehensions, list methods such as `append` |
| Text concatenation, equality, `len`, `text.trim`, `text.split_part` | String slicing, implicit conversion, arbitrary string methods |
| Number times a known unit; quantity divided by a unit | Arbitrary dimensional algebra or implicit unit conversion |

Ordinary numeric division produces a float. Volume and duration support
same-dimension arithmetic and ordering; quantity rules are below. A condition
must be Boolean: use `self.count > 0`, not `self.count`. Text also supports `+`
for concatenation and `==`/`!=` for exact comparisons.
Lists have no implicit truth value, whole-list comparisons or arithmetic.

**AutoSuite restriction:** although SciLoom accepts `and` and `or`,
this target rejects them. Use [nested conditions](../troubleshooting.md#autosuite-rejects-boolean-combinations).

## Physical quantities

Import `Volume`, `Duration`, `uL`, `mL`, `L`, `s`, `minute` and `hour` from
`sciloom`. Declare them as inputs, outputs or initialized state just like speed.
Multiplying a runtime number by a unit constructs the corresponding quantity.

| Operation | Example | Result |
| --- | --- | --- |
| Add/subtract the same dimension | `self.volume - 1 * mL` | Volume, possibly negative |
| Multiply/divide by a number | `self.interval / 2` | Duration |
| Compare the same dimension | `self.interval < 1 * minute` | bool |
| Divide like quantities | `self.volume / self.reference_volume` | float |
| Express a quantity in a unit | `self.volume / mL` | float |
| Construct from a number | `self.number * mL` | Volume |

Volume and duration also support unary `+` and `-`. Speed supports scaling and
like-quantity ratios, while retaining its nonnegative constraint; speed addition,
negation and ordering remain unsupported. Booleans are never numeric quantities.
Results use floating arithmetic, so unit conversions can have ordinary rounding.

**AutoSuite restriction:** quantity division currently requires a literal nonzero
divisor. Speed scaling requires a literal nonnegative factor, positive for
division. Runtime number-to-speed construction needs a sign check and is refused
until runtime failure propagation is verified. Volume/duration lists support
whole-list construction, copying and calls; guarded indexing awaits the same
verification. The reference interpreter supports these operations and reports
invalid values when they occur.

The [quantity example](../../examples/quantity-conversion.md) shows conversion in
a complete function. A Duration value stores an interval; waiting and timers are
separate operations.

## Text

Declare text with `Input[str]`, `Output[str]` or an initialized `Var[str] = ""`.
Import `text` from `sciloom` for the two runtime helpers:

| Operation | Result |
| --- | --- |
| `self.name + "_processed"` | A new text value |
| `len(self.name)` | Number of Unicode code points, without normalization |
| `text.trim(self.name)` | Removes space, tab, CR and LF at both ends; retains other Unicode whitespace |
| `text.split_part(self.name, ",", 1)` | Second comma-separated part; empty parts are retained, missing parts return `""` |

Split delimiters must be nonempty, and indices must be nonnegative integers,
excluding bool. Use `self.name != ""` for a condition. Runtime helpers belong
inside `@runtime`; ordinary host Python can use its own string methods.

**AutoSuite restriction:** split currently requires a literal nonempty delimiter
and literal nonnegative index. Text-list values support construction, whole-list
copies and function parameters; indexed reads/writes needing runtime bounds checks
are refused until AutoSuite failure propagation has been verified. Reference
execution supports these operations. Unicode length, whitespace and encoding
equivalence on AutoSuite still require Executor validation.
AutoSuite length currently accepts literal BMP text only: it rejects lengths of
runtime text because that text can contain non-BMP characters whose native count
has not been verified.

The [label example](../../examples/prepare-labels.md) shows a complete program.

## Statements

| Supported | Outside the source language |
| --- | --- |
| Assignments to declared runtime fields; `+= -= *= /=` | Assignments to local names or undeclared fields |
| Assignments and augmented assignments to list elements | Slicing assignments, such as `self.items[1:] = ...` |
| `if` / `elif` / `else`, `while` | `for`, `break`, `continue`, `while ... else` |
| Calls to child Functions stored on `self` | Arbitrary helper calls, calls nested in expressions |
| Device property assignment and declared commands | Property reads or augmented property assignments |
| Whole `if/elif` conditions using `comptime` queries | Combining these queries with `and` / `or` or runtime arguments |
| `pass`, docstrings | `return`, `try`, `with`, `assert`, `del`, nested definitions |

See the [device reference](devices-and-targets.md) for property, command and
query forms.

## Lists and indices

`self.result = self.values` copies the complete list. Changing
`self.result[0]` afterwards does not change `self.values[0]`. A child
also receives copies of list inputs, and its output lists are copied back.

Indices start at zero and must be integers, excluding Booleans. Negative and
out-of-range indices are execution errors; writes never extend a list.
When each call should scan the list from the beginning, reset the loop index
at the start of the method.
See [lesson 4](../tutorial/lists-and-loops.md).

**AutoSuite restriction:** assign each output list as a whole on every return
path, before reading or updating its elements. A loop can run zero times.
An empty assignment is a valid empty result but supplies no elements to update.

## Child Function calls

| Result | Call form |
| --- | --- |
| No outputs | `self.child(...)` |
| One output | `self.result = self.child(...)` |
| Several outputs | `self.a, self.b = self.child(...)`, in output declaration order |

Supply every input exactly once, by position or keyword. Output destinations
must be whole fields. To use a result in an expression or a list element,
store it in a field first. See [composition](../advanced/composition.md).

**AutoSuite restriction:** recursive calls, direct or indirect, are refused.
