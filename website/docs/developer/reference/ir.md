# Semantic IR and JSON v4

Use `sciloom.core.ir` to construct or exchange typed programs. The
[direct-list example](../../examples/list-ir.md) builds a complete Program without
the Python DSL. Experiment authors normally use Function instead.

Program selects an entry FunctionIR and contains referenced functions, resources
and a declarative device-type directory. Frozen semantic nodes retain structured
If/While/ForEachZone, calls, list operations, property configuration and lifecycle intent.
They do not contain AutoSuite UUIDs, task encodings or hidden context parameters.

## Types, ownership and identity

Variables have an owner function, role and value type. Scalars are INTEGER, REAL,
BOOLEAN, TEXT, ROTATIONAL_SPEED, VOLUME and DURATION internally; a ListType contains one scalar element
type. Public Python authors use native int/float/bool/str rather than these IR enums.
Internal variables require literal initializers. Input/output defaults are not
supported. Conditions are Boolean and list element types are invariant.

Volume and duration literals hold finite SI numbers (m³ and seconds). Unit
construction and conversion reuse typed Binary/Literal operations: multiplying
REAL by a VOLUME literal yields VOLUME; dividing two VOLUME values yields REAL.
No Python unit object enters JSON. Quantity constraints apply to intermediate
values too, so a negative speed cannot be hidden inside a later comparison.

`Unary` also represents numeric magnitude and rounding: `UnaryOp.ABSOLUTE`
preserves its numeric or signed-quantity operand type; `UnaryOp.FLOOR` and
`UnaryOp.ROUND` require INTEGER/REAL and return INTEGER. ROUND uses ties-to-even.
Their wire values are `abs`, `floor` and `round`. These additions reuse the v4
record structure and leave earlier JSON unchanged. Type checking, reference
execution and target generation dispatch explicitly over the operation enum.

IDs identify node occurrences in a program-wide namespace. Two reads of one
variable use different node IDs but the same symbol_id. References cannot cross
function ownership. Calls use callee variable IDs for their complete I/O bindings.
Global ownership and public Application APIs remain deferred.

Use ListLiteral, ListLength, ListGet and ListSet for list intent. DeviceResource,
ConfigureProperty, StartAgitation, StopAgitation and DeviceCommand retain equipment
intent. DeviceIf and its typed predicates retain branches until specialization.

`Program.resources` holds the `Resource` union: `DeviceResource` or
`TimerResource`. A timer has an `owner_id` pointing to a FunctionIR and a public
declaration `name`; only that function may start or wait on it. `StartTimer`
captures or resets the origin, `Wait` pauses for a Duration, and `WaitUntil`
waits until a Duration has elapsed since that origin. These are ordered
statements, not expressions. See the [direct timing example](../../examples/timing-ir.md).
Device bindings apply only to DeviceResource. Specialization removes timers
whose owning functions become unreachable; existing device wire fields do not
change. Definite timer starts are checked after device specialization.

## Zone values and traversal

`ZoneType` is separate from scalars and lists. `ZoneLiteral`, `ZoneFind`,
`ZoneCombine`, `ZoneLength` and `WellName` retain location intent. `ZoneGet(value,
index)` evaluates the selection and index once in that order and returns a
one-well Zone. The index must be a nonnegative INTEGER within the selection.

`ForEachZone(target, value, body=(), fragment_size=1)` captures `value` once,
checks divisibility, then assigns each fragment to a Function-owned internal Zone
variable before running `body`. Empty input preserves the target. Body writes
cannot change the captured selection; the final target value persists without
an implicit restore. Nested loops capture independently, even when reusing a
target. Body writes do not establish definite configuration or timer starts after
a potentially empty loop. Specialization recursively selects branches inside it.

Both are additive v4 kinds. The [direct traversal example](../../examples/zone-traversal-ir.md)
shows JSON round trips, grouping and reference execution. AutoSuite only accepts
size-one traversal until its index/divisibility failure checks are verified.

## Typed CSV statements

`ReadCsv` is an ordered, result-producing statement. `CsvReadMode` selects one
row or whole columns; `CsvErrorPolicy` selects fatal failure or status results.
Each `CsvColumn` stores a typed selector, optional unit literal and default.
Distinct target references bind the whole result tuple. No CSV parser function,
Python type object or vendor result code is stored in JSON. The
[direct CSV example](../../examples/csv-read-ir.md) demonstrates these additive v4
records; new readers still preserve old canonical documents unchanged.

## Validation and serialization

`validate(program)` returns a tuple of Diagnostic records. `to_dict/from_dict`
operate on mappings; `to_json/from_json` operate on strings. Import and export
validate and raise IRValidationError on invalid data.

```python
from examples.developer.list_ir import build_program
from sciloom.core.ir import from_json, to_json, validate

program = build_program()
assert validate(program) == ()
assert from_json(to_json(program)) == program
```

| Rule | Detail |
|---|---|
| envelope | `kind="Program"` and `format_version=4`; earlier versions are not upgraded |
| records | each carries the stable `kind` declared by its dataclass's `__ir_kind__`; enums are strings, tuples become arrays |
| rejected on import | unknown fields or kinds, duplicate keys, wrong scalar types, `NaN`, `Infinity`; node ids are required, never generated |
| export | includes defaults, sorted keys, two-space indentation, a final newline; bodies and bindings keep their order; exported mappings are detached |
| stability | existing v4 kinds, field names, defaults and meanings are fixed; implementation refactors preserve canonical JSON and generated AutoSuite UUIDs |

The codec derives structure from dataclass field annotations. Each reachable
record declares its own unique `__ir_kind__: ClassVar[str]`, including nested
contracts and SourceSpan. Renaming a Python class does not rename its wire kind.
Missing, inherited-only or duplicate declarations produce `ir_schema` diagnostics.

New vocabulary can extend v4 without rewriting old documents. Newer versions must
still read existing valid v4 programs; older versions may explicitly reject kinds
or types they do not support. A change to an existing meaning requires a separate
format decision and explicit migration design, not an implicit import conversion.

SourceSpan records one-based lines and zero-based UTF-8 byte columns. Source IDs
and spans survive round trips. Lowering records the absolute path of the defining
file, so paths identify the generating checkout; the developer examples rewrite
them relative to the repository root before writing their companion files. JSON is declarative data: implementation IDs never
cause dynamic Python imports. See [binding and specialization](pipeline.md).
