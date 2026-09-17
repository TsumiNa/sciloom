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
| `Zone` | Ordered unique wells; no list nesting or implicit truthiness; see [locations](zones.md) |

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
| `abs(value)`, `math.floor(value)`, `round(value)` | `round(value, ndigits)`, other math functions |

Ordinary numeric division produces a float. Volume and duration support
same-dimension arithmetic and ordering; quantity rules are below. A condition
must be Boolean: use `self.count > 0`, not `self.count`. Text also supports `+`
for concatenation and `==`/`!=` for exact comparisons.
Lists have no implicit truth value, whole-list comparisons or arithmetic.

**AutoSuite restriction:** although SciLoom accepts `and` and `or`,
this target rejects them. Use [nested conditions](../troubleshooting.md#autosuite-rejects-boolean-combinations).

## Numeric functions

Use `abs(self.value)` for magnitude and `floor(self.value)` after importing
`floor` from `math` for the greatest integer no larger than a number.
`round(self.value)` returns the nearest integer, choosing the even integer on
an exact half: `round(2.5)` is 2, `round(3.5)` is 4, and `round(-2.5)` is −2.
Only the one-argument forms are supported. Imported aliases and `math.floor`
work too; a user-defined function with the same name is not a runtime operation.

`abs` preserves `int` or `float`, and also accepts Volume and Duration.
`floor` and `round` return `int`. Convert a quantity to a number first, for example
`floor(self.amount / mL)`. Booleans, text and lists are not numeric arguments.
Reference inputs and arithmetic results must be finite.

**AutoSuite restriction:** `abs` and `floor` use the documented native functions.
Floor and round of an integer keep the integer unchanged. Rounding a float is
currently refused: AutoSuite's rule for half values and an equivalent expansion's
range have not been verified. The reference interpreter supports Python's rule.
Large-number reference results do not establish AutoSuite's numeric limits.

The [portion calculation](../../examples/numeric-operations.md) combines quantity
conversion, floor and magnitude without controlling equipment.

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

### Temperature values

Import `Temperature`, `TemperatureDifference`, `TemperatureRate`, `degC`,
`kelvin`, `delta_degC`, `delta_kelvin`, `degC_per_min` and `kelvin_per_s`
from `sciloom`. They can be declared in Input/Output/Var and homogeneous lists.
Absolute values store kelvin (0°C = 273.15 K), differences store signed kelvin,
and rates store signed K/s. Booleans and nonfinite values are rejected.

| Operation | Result |
| --- | --- |
| `20 * degC` | Absolute 293.15 K; source construction requires a numeric literal |
| Absolute − absolute | TemperatureDifference |
| Absolute ± difference; difference + absolute | Temperature, rejecting results below 0 K |
| Same-type comparison | bool |
| Difference/rate arithmetic and numeric scaling | Same difference/rate type |
| Difference/rate divided by the same type or its unit | float |

Absolute + absolute, absolute scaling/ratios and cross-dimension multiplication
are rejected. A runtime numeric field multiplied by `degC` is not an implicit
cast; supply a typed Temperature input. Signed difference/rate unit construction
can use runtime numbers. Logging and CSV append retain canonical values, while
thermal CSV reads are explicitly unsupported until a conversion contract exists.
AutoSuite compilation rejects thermal types pending verified native encodings
and range behavior. Core/reference support does not prove vendor conversion or
physical equivalence. See the [runnable example](../../examples/temperature-values.md).

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
| `if` / `elif` / `else`, `while`, Zone `for` with a `Var[Zone]` target | List/general Python iteration, `break`, `continue`, loop `else` |
| Calls to child Functions stored on `self` | Arbitrary helper calls, calls nested in expressions |
| Device property assignment and declared commands | Property reads or augmented property assignments |
| `self.label[zone] = text`, `self.text = self.label.get(zone, default="")` for a declared `WellProperty` | Indexed metadata reads, augmented writes, non-text properties or reads inside larger expressions |
| `log(value, category=..., stream=...)` | Logging lists, automatic object formatting or using log as a result |
| `notify(message)` | Timeout, automatic confirmation, cancellation branches or a returned value |
| `self.text = request_text(message, timeout=...)`; `self.answer = ask_yes_no(message, timeout=...)` | Nested expressions, discarded results, fallback on cancel/Stop/timeout; AutoSuite generation is pending native verification |
| `self.stamp = now_text(format)` | Clock reads inside larger expressions, runtime format strings |
| `wait(duration)`, declared Timer `start()` and `wait_until(duration)` | Contact/setpoint waits, automatic stop, shared Timer objects |
| Whole `if/elif` conditions using `comptime` queries | Combining these queries with `and` / `or` or runtime arguments |
| `with at(self.shaker, self.location):` | General context managers, `as` targets, multiple contexts or nested selection of the same device; AutoSuite emission is currently gated |
| `pass`, docstrings | `return`, `try`, `with`, `assert`, `del`, nested definitions |

See the [device reference](devices-and-targets.md) for property, command and
query forms.

## Record values

Import `log` from `sciloom` and call it inside `@runtime`:

```python
log(self.volume, category="recipe", stream="dispensed_volume")
```

The value can be `int`, `float`, `bool`, `str` or a supported physical quantity.
Category and stream are text and can come from inputs or text expressions. The
program captures value, category, then stream once in that order; a later
assignment does not change an earlier log. This is also the evaluation order
when the two keywords are written in a different order.

Logging records the value you supply. It does not measure an instrument, return
a value or select a CSV file. Use the [complete logging example](../../examples/record-values.md)
to generate an AutoSuite function. Application log storage and the resulting
records still need verification in the deployed AutoSuite environment.

## Request confirmation

Import `notify` from `sciloom` and place it before the steps that need confirmation:

```python
notify("Samples are ready. Confirm to continue.")
```

The message can include runtime text, for example `"Confirm sample " + self.label`.
Its value is captured when the step begins. The next step waits for OK; this call
has no return value, timeout or automatic response. It belongs inside `@runtime`,
not in the constructor or compilation script.

The [confirmation example](../../examples/confirm-samples.md) generates an AutoSuite
function with a message followed by a log. The generated OK dialog still needs
Executor validation of blocking and continuation on the deployed host.

## Read wall time

Import `now_text` from `sciloom`. Assign its result to one declared text field
before using it in another expression:

```python
self.stamp = now_text("%Y-%m-%d_%H%M%S")
self.path = self.directory + "/" + self.stamp + ".csv"
```

Each call reads the clock once when the generated function runs. Reusing
`self.stamp` reuses that captured value. Compilation does not read the clock.
The format must be host-time text: a literal, a module/closure text constant,
or an ordinary `self` setting. It cannot come from a runtime input.

| Directive | Field |
| --- | --- |
| `%Y` | Year, at least four digits |
| `%m`, `%d` | Two-digit month and day |
| `%H`, `%M`, `%S` | Two-digit 24-hour hour, minute and second |
| `%%` | Literal percent sign |

Other characters appear as written. Unsupported directives and an unmatched
`%` are rejected. Empty or literal-only formats still perform a clock read.
AutoSuite uses local time; no timezone conversion or unique-name guarantee is
provided. The [filename example](../../examples/timestamp-path.md) is a complete
program. Calendar boundaries, local daylight-saving changes and format encoding
still need Executor validation.

## Wait and timer

Import `Timer`, `s` and `wait` from `sciloom`. Declare `timer: Timer` on the
Function, alongside its input and output declarations. Inside `@runtime`:

```python
self.timer.start()
wait(2 * s)
self.timer.wait_until(5 * s)
```

This waits a total of five seconds from the timer start: two seconds first,
then the remaining three. `wait()` pauses for an interval; `wait_until()` pauses
until an elapsed threshold. Repeating `start()` resets the origin. If the
threshold has passed, `wait_until()` continues immediately.

Both calls take a nonnegative Duration. They preserve the current device
configuration and running state. Use `self.shaker.stop()` when the procedure
should stop agitation; waiting does not schedule an automatic stop.

A Timer belongs to one Function instance. Do not construct one in `__init__` or
assign another Function's timer to it. Child calls consume the same elapsed
time axis, but own their own timers. Every reachable wait must have a prior
start in the current entry invocation; a previous call is not an implicit start.
Starting only inside a conditional or zero-iteration loop may leave a path
without a start.

**AutoSuite restrictions:** waits currently require literal durations within
0–79,999 hours (an ordinary host setting such as `self.delay = 5 * s` also lowers
to a literal). Runtime inputs need range/failure checks and are refused until
failure propagation is verified. All starts/resets of one timer must lie in
one lexical Macro scope; waits may stay there or descend into its branches and
loops. A start in a branch followed by a wait outside that branch is refused.
The reference interpreter supports broader Function scope.

The [timed agitation example](../../examples/timed-agitation.md) is a complete
program. Generated waits disable the cancel-wait button. Actual timing, resets,
scope and cancellation settings remain subject to Executor verification.

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

## CSV files

CSV reads return tuples and always require unpacking even for a single
column. `csv.append_row(path, values=(...))` is a standalone operation;
`csv.try_append_row(...)` assigns one integer status to a field. See
[CSV files](csv.md) for their distinct read/append and error rules. Both have
reference execution; AutoSuite compilation remains gated on platform evidence.

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
