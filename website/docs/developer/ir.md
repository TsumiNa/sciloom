# Semantic IR and JSON v4

Use `sciloom.core.ir` to construct or exchange typed programs. The
[direct-list example](../examples/list-ir.md) builds a complete Program without
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

JSON requires kind="Program" and format_version=4. Records carry their public
dataclass kind; enums use strings and tuples become arrays. Unknown fields/kinds,
earlier versions, duplicate keys, wrong scalar types, NaN and Infinity fail.
Exports include defaults, sorted keys, two-space indentation and a final newline;
ordered bodies and bindings keep their order. Exported mappings are detached.

SourceSpan records one-based lines and zero-based UTF-8 byte columns. Source IDs
and spans survive round trips. Paths identify the generating checkout and can
differ between environments. JSON is declarative data: implementation IDs never
cause dynamic Python imports. See [binding and specialization](compiler.md).
