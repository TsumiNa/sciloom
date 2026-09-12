# Function compilation to ASFP

The first compiler sequence is implemented: Python Function instances lower to
typed semantic IR, then a thin Serialization IR and AutoSuite ASFP XML. The target
is AutoSuite 2.47.1.1. A typed individual-shaker agitation adapter is also available.
Application, global binding and other device tasks remain deferred.

## Run the example

```bash
uv run python examples/function_call.py
```

This writes `examples/function_call.asfp` outside the reference corpus. The example is based on `Test12_FIXED_CallBinding_RealInOut.asfp`:
an identity function accepts real `x` and writes real `y`; its caller passes `2.5`
and binds the output to internal variable `result`. Function names and generated
IDs differ; structure and parameter binding relationships match the fixture.

## Public API

```python
from sciloom.backends.autosuite import AutoSuiteTarget

result = program.compile(target=AutoSuiteTarget())
result.target_id
result.diagnostics
result.artifact.content     # UTF-8 XML bytes
result.artifact.media_type  # application/xml
result.artifact.suffix      # .asfp
result.write("dist/program.asfp")
```

The target is explicit. `AutoSuiteTarget()` selects its supported default vendor
version, 2.47.1.1; unknown versions raise `ValueError`. A different target implements
the protocol in `sciloom.core.compiler`. IR errors raise `IRValidationError`; target
restrictions and XML failures raise `CompilationError`, both with diagnostics.
`.compile()` never writes files or changes the source instance; `.write()` creates
parents and replaces the requested file. There is no separate transpile API.
The generic result has no XML-specific field. Backend developers can inspect
`backends.autosuite.codegen.lower_asfp` and its immutable XML records separately.

## Agitation example

`uv run python examples/agitation.py` writes `examples/agitation.asfp` using
`function.compile(target=target)`. Both user examples focus on Python authoring
and ASFP export; neither exposes IR or executes a reference interpreter.
The agitation function retains speed and enabled as runtime input parameters.
[Agitation semantics](15_AGITATION_SEMANTICS.md) describes the source API and
explicit IndividualShakerBinding configuration; the
[mapping record](../autosuite/docs/16_AGITATION_MAPPING.md) identifies the real
application/function evidence, fixed-zone addressing and inactive stop defaults.

## Developer workflow

From the repository root, run:

```bash
uv run python -m examples.developer.agitation_ir
```

This separate example reuses ConfigureAgitation, obtains its Program through
`.to_ir()`, saves `examples/developer/agitation_ir.json`, reloads it with `from_json`
and checks start/stop behavior with Interpreter. It generates no ASFP. Reference
execution and JSON interchange are development tools, not required compilation
steps for experiment authors.

Developers can inspect `result.semantic_ir` after compilation or compile a
loaded Program with `compile_ir(program, target=target)`. Loaded agitation IR
needs the same explicit zone/shaker bindings as the Python Function.

## Layer boundaries

```mermaid
flowchart LR
    Python["Function instance"] --> Lower["Python AST lowering"] --> Semantic["Typed Program"]
    JSON["JSON import"] --> Semantic
    Semantic --> Validate["Shared semantic validation"]
    Validate --> Target["Explicit target validation"] --> Backend["ASFP mapping and target IDs"]
    Backend --> SIR["Immutable SerializationIR / XmlNode"]
    SIR --> XML["ASFP XML bytes"]
```

`frontends/python/model.py` provides the model API; `frontends/python/lowering.py` analyzes source; `core/ir/` holds
semantics/validation; `core/compiler.py` coordinates format-independent compilation; `backends/autosuite/codegen.py` maps the
target; `backends/autosuite/xml.py` contains immutable XML records and encoding. The installed
package needs no reference corpus or third-party runtime dependencies to compile.

The backend owns `typeid`s, UUIDs, parameter IDs, Macro containers and XML defaults.
It currently retains fixed `.1` type identifiers. The suffix's formal meaning and
compatibility across vendor versions remain an
[open confirmation item](../autosuite/docs/05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md#typeid-suffix-provisional-assumption-and-open-question);
no suffix calculation or variant handling is implemented.
Internal variables become declarations on an enclosing Macro. Parameter-only
functions can contain assignments/calls directly. While/If become conditional
Macros; If/Else branches own `components` inside `SATaskCondition` tasks. Else-If
is represented as nested If/Else inside the Else branch.

Exports establish parameter types `realnumber`, `integer`, `bool` and storage
codes `5`, `3`, `11`. Rotational-speed parameters use `angularspeed`;
internal speed variables use code `5`, SI unit `1/s` and display unit `rpm`. Boolean storage uses `-1/0`, expressions use `true/false`.
Integer/boolean unit metadata follows the observed `siunit=1, unit=s` form; this
serialization convention does not introduce a physical time type into the IR.

## Determinism and evidence

Target UUIDs derive from a digest of Program and canonical deployment bindings,
plus the target version and object role/ID. Binding tuple order is irrelevant.
Source spans are excluded. Recompilation produces identical bytes; different
specializations receive distinct target IDs. Timestamps use a fixed zero epoch.
Unsafe expression identifiers are mapped to safe local names, with references and
call bindings using the same mapping. Macro counters avoid declared variable names.
The manual requires variable names to start with an ASCII letter; JSON names
starting with an underscore are therefore mapped even though Python would allow them.

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
