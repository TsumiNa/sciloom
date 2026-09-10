# Function compilation to ASFP

The first compiler sequence is implemented: Python Function instances lower to
typed semantic IR, then a thin Serialization IR and AutoSuite ASFP XML. The target
is AutoSuite 2.47.1.1. Application, global binding and device tasks remain deferred.

## Run the example

```bash
uv run python examples/function_call.py
```

This writes `dist/function_call.asfp` and `dist/function_call.ir.json` outside the
reference corpus. The example is based on `Test12_FIXED_CallBinding_RealInOut.asfp`:
an identity function accepts real `x` and writes real `y`; its caller passes `2.5`
and binds the output to internal variable `result`. Function names and generated
IDs differ; structure and parameter binding relationships match the fixture.

## Public API

```python
result = program.compile()  # default target: autosuite-2.47.1.1
result.semantic_ir
result.serialization_ir
result.diagnostics
result.artifact             # UTF-8 XML bytes
result.write("dist/program.asfp")
```

`Target.AUTOSUITE_2_47_1_1` or its string value can be supplied as `target`.
Unsupported targets raise `ValueError`. Invalid semantics/XML text raise
`IRValidationError` with diagnostics. Successful results currently have no
diagnostics. `.write()` creates parents and writes/replaces the requested file.
`.compile()` itself does not write files or change the source instance.
`.to_ir()` returns only the semantic model. There is no separate `transpile()` API.

JSON authoring uses the same compiler:

```python
from pathlib import Path
from sciloom import compile_ir
from sciloom.ir import from_json

package = from_json(Path("dist/function_call.ir.json").read_text())
compile_ir(package).write("dist/from_json.asfp")
```

## Layer boundaries

```mermaid
flowchart LR
    Python["Function instance"] --> Lower["Python AST lowering"] --> Semantic["Typed Package"]
    JSON["JSON import"] --> Semantic
    Semantic --> Validate["Shared semantic validation"]
    Validate --> Backend["ASFP mapping and target IDs"]
    Backend --> SIR["Immutable SerializationIR / XmlNode"]
    SIR --> XML["ASFP XML bytes"]
```

`frontend.py` provides the model API; `lowering.py` analyzes source; `ir/` holds
semantics/validation; `compiler.py` coordinates compilation; `asfp.py` maps the
target; `serialization.py` contains immutable XML records and encoding. The installed
package needs no reference corpus or third-party runtime dependencies to compile.

The backend owns `typeid`s, UUIDs, parameter IDs, Macro containers and XML defaults.
Internal variables become declarations on an enclosing Macro. Parameter-only
functions can contain assignments/calls directly. While/If become conditional
Macros; If/Else branches own `components` inside `SATaskCondition` tasks. Else-If
is represented as nested If/Else inside the Else branch.

Exports establish parameter types `realnumber`, `integer`, `bool` and storage
codes `5`, `3`, `11`. Boolean storage uses `-1/0`, expressions use `true/false`.
Integer/boolean unit metadata follows the observed `siunit=1, unit=s` form; this
serialization convention does not introduce a physical time type into the IR.

## Determinism and evidence

Target UUIDs derive from a digest of the semantic package plus object role/ID.
Source spans are excluded. Recompilation produces identical bytes; different
specializations receive distinct target IDs. Timestamps use a fixed zero epoch.
Unsafe expression identifiers are mapped to safe local names, with references and
call bindings using the same mapping. Macro counters avoid declared variable names.

Tests compare complete normalized trees against Test12, Test10_FIXED3, Test09 and
Test08. They ignore times, selected function names, function-list order and concrete
UUID spellings. A consistent UUID renaming preserves reference relationships;
deliberately corrupting a call parameter ID makes comparison fail. Tests also cover
JSON/Python equivalence, source preservation, boolean storage, nested control flow,
safe names and file output.

This establishes structural/reference validation, not Executor acceptance. No
official function XSD is supplied. On an AutoSuite host, import the ASFP into an
appropriate application and validate with Executor simulation before claiming
runtime acceptance. Original reference files are unchanged.
