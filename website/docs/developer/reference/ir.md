# Semantic IR and JSON v4

Use `sciloom.core.ir` to construct or exchange typed programs. The
[direct-list example](../../examples/list-ir.md) builds a complete Program without
the Python DSL. Experiment authors normally use Function instead.

Program selects an entry FunctionIR and contains referenced functions, resources
and a declarative device-type directory. Frozen semantic nodes retain structured
If/While, calls, list operations, property configuration and lifecycle intent.
They do not contain AutoSuite UUIDs, task encodings or hidden context parameters.

## Types, ownership and identity

Variables have an owner function, role and value type. Scalars are INTEGER, REAL,
BOOLEAN and ROTATIONAL_SPEED internally; a ListType contains one scalar element
type. Public Python authors use native int/float/bool rather than these IR enums.
Internal variables require literal initializers. Input/output defaults are not
supported. Conditions are Boolean and list element types are invariant.

IDs identify node occurrences in a program-wide namespace. Two reads of one
variable use different node IDs but the same symbol_id. References cannot cross
function ownership. Calls use callee variable IDs for their complete I/O bindings.
Global ownership and public Application APIs remain deferred.

Use ListLiteral, ListLength, ListGet and ListSet for list intent. DeviceResource,
ConfigureProperty, StartAgitation, StopAgitation and DeviceCommand retain equipment
intent. DeviceIf and its typed predicates retain branches until specialization.

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
