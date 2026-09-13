# AGENTS.md

Instructions for humans and coding agents working on this package.

## Additional repository instructions

Agents must discover and read the applicable instruction files under
[`.github/instructions/`](.github/instructions/) before starting work. These are
required repository rules, not optional reference material.

- Use each file's `applyTo` patterns and `description` to determine its scope.
  Read the full contents of every applicable file before performing the related work.
- Apply workflow and environment instructions according to the activity being
  performed, including files without `applyTo`. Read shell-environment rules
  before terminal work and branch/PR rules before making changes.
- Read and follow the [in-branch API compatibility rules](.github/instructions/in-branch-api-compat.instructions.md)
  before evolving in-progress APIs within a branch or adding compatibility wrappers,
  adapter layers, deprecated aliases or parallel interfaces.
- Follow the [example output documentation rules](.github/instructions/example-output-documentation.instructions.md)
  when creating or updating examples: embed short results in module docstrings and
  keep long generated results in same-base-name companion files beside their code.
- Recheck applicable instructions when the task expands to new files or activities.
  Do not assume the IDE or agent runtime has loaded them automatically.
- Explicit user instructions and higher-priority system/developer instructions
  take precedence over repository instruction files.

## 1. Architecture invariants

1. **Typed SciLoom Semantic IR is the semantic source of truth.**
2. The primary code frontend is a **restricted Python source language**. Python AST/CST analysis is intentional; arbitrary Python compatibility is not a goal. The implemented subset is documented in `docs/12_PYTHON_FRONTEND.md`.
3. **Class-level declarations define the static SciLoom runtime schema.** Use `Input[T]`, `Output[T]` and `Var[T]` with native `float`, `int`, `bool` or physical quantity types. `Var` needs an explicit initial value. Unwrapped annotations are host-time data. There is no `Local[T]` wrapper; field scope follows the owning model. Application/global support remains deferred; future Function `GlobalRef[T]` fields explicitly reference Application state.
4. **The program/function instance is the compilation unit.** `__init__` and ordinary Python specialize/compose the instance before `instance.compile()`.
5. Python is host/generation-time by default. There is no baseline `@comptime` decorator. Explicit decorators/registered roles mark AutoSuite runtime methods and event entry points (`runtime`, `main`, `on_start`, `on_error`, `on_stop`, etc.).
6. `__init__` must not silently create new runtime fields in v1. Runtime field schema belongs at class level; instance attributes are compile-time values/components unless explicitly modeled otherwise.
7. `.compile()` belongs on the SciLoom model instance (typically inherited from a common base) and should return a compile result without mutating the semantic meaning of the source instance.
8. xyflow and AI tooling must operate on the same semantic IR, directly or through the deterministic Python frontend.
9. `.app/.asfp` XML is a versioned serialization backend. Do not leak `typeid`, UUID or parameter-ID mechanics into the public DSL unless unavoidable.
10. Keep a thin Serialization IR/backend layer between Semantic IR and XML.
11. Historical ASPY is reference material only. Do not extend it as the future user-facing language.
12. Deprecated COM integration is not an implementation option.
13. ArkSuite assumptions remain deferred until vendor documentation is available.

## 2. Evidence hierarchy

When facts conflict, prefer in this order:

1. `autosuite/app/config20260909_polymerization.app`
2. functions extracted from that app
3. AutoSuite-produced FIXED/re-exported schema fixtures
4. latest standalone `.asfp` snapshots
5. AutoSuite manual for documented semantics
6. historical generated XML candidates (comparison evidence only)
7. conversational reconstruction/inference

The manual is authoritative for documented **semantics**, but not for `.asfp/.app` XML serialization; no official function/application XSD is present in the supplied manual.

## 3. Do not mutate evidence silently

Raw APP/ASFP files, archives, manual, extracted XML and schema fixtures under `autosuite/` are evidence. Do not rewrite them to make a serializer test pass. Create new generated outputs elsewhere and compare them. `autosuite/MANIFEST.csv` records current reference hashes; `autosuite/catalogs/relocation.csv` records the original locations of preserved material.

## 4. Python frontend rules

Runtime state must be statically inspectable from the class definition, e.g.:

```python
class Example(Function):
    source: Input[Zone]
    index: Var[int] = 0
```

`__init__` is normal Python and may specialize the program:

```python
def __init__(self, *, valve_group_size=8):
    self.valve_group_size = valve_group_size
```

Compiled AutoSuite runtime methods should use ordinary Python syntax where target semantics are equivalent (`if`, `elif`, `else`, `while`, assignment, calls, expressions, indexing, constrained loops).

Do not require users to write IR constructors such as `If(...)` or `While(...)` unless they are internal APIs.

A typical lifecycle is:

```python
program = MyFunction(option=...)
artifact = program.compile(target=...)
```

During AST/CST lowering, a `self.attr` reference is resolved against the registered class runtime schema first. Registered runtime fields become target symbol references; ordinary specialized instance attributes are compile-time values/components and may be constant-folded or used during lowering.

Runtime source initially comes only from ordinary `.py` files. Do not add Notebook,
interactive or `exec()` support to the first compiler. Internal variable defaults
are target initial values, not an implicit reset on every call; use explicit runtime
assignment when a reset is required.

Future globals are declared on Application and bound explicitly with
`function.bind_globals(name=app.ref("name"))`. `GlobalRef[T]` denotes shared runtime
state, not a copied host value. Python module globals never become AutoSuite globals
implicitly. Global binding and Application compilation are outside the first
Function compiler sequence; see `docs/refactor/semantic-ir/00-overview.md`.

## 5. Error model

Hardware/runtime faults are fatal by default. Do not implement Python `except` as silent catch-and-continue unless the target AutoSuite primitive genuinely supports recovery.

Proposed fatal-handler syntax:

```python
try:
    critical_operation()
except AutoSuiteError as err:
    log(err)
    alert_maintenance(err)
    raise
```

The backend may lower lexical handlers to generated fault-region state plus the single AutoSuite `OnError` function. `raise` preserves fatal propagation. Recoverable task/result errors are a separate semantic category.

## 6. Validation layers

Aim for:

1. class schema / Python frontend validation
2. instance specialization validation
3. symbol/type/unit validation
4. AutoSuite semantic validation
5. configuration/device/zone validation
6. XML/reference validation
7. real `AutoSuiteExecutor.exe /r /sim 100 /s /c` integration gate

Static XML parse success is not equivalent to Executor acceptance.

## 7. Before changing serialization

Read:

- `autosuite/docs/04_SCHEMA_EXTRACTION_METHOD.md`
- `autosuite/docs/05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md`
- `autosuite/docs/06_SEMANTIC_TO_XML_MAPPING_REFERENCE.md`
- `autosuite/docs/07_GOLDEN_FIXTURE_MATRIX.md`
- `autosuite/schema/empirical_type_catalog.*`
- `autosuite/schema/type_templates/`

Prefer corpus-derived templates and explicit typed adapters for device-specific task payloads.

## 8. Tests

Run at minimum:

```bash
uv run pytest src/sciloom
uv run mypy
python autosuite/tools/smoke_test.py
python autosuite/recipe/validate_recipe.py autosuite/recipe/input_0908.csv
```

Run the experiment-author examples with `uv run python examples/function_call.py`
and `uv run python examples/agitation.py`. Run the list author examples with `uv run python examples/scale_values.py` and
`uv run python examples/non_zero_array_min.py`. Also run the developer example
with `uv run python -m examples.developer.agitation_ir` from the repository root.
Run `uv run python -m examples.developer.list_ir` for direct list IR and JSON v4.
Run `python autosuite/tools/audit_corpus.py` after reference changes. Syntax-check `examples/proposed_frontend/*.py`. On the AutoSuite host, generated `.app` files must additionally pass Executor simulation. The historical compiler, ASPY inputs and text views have been removed; refactor work starts from the retained XML and semantic documentation.

## 9. Documentation location

Keep internal project/design Markdown under `docs/` and AutoSuite-specific reference Markdown under `autosuite/docs/`. Root Markdown is limited to `README.md` and `AGENTS.md`.

Public English documentation lives under `website/docs/`; it is the only website
source tree. Website configuration, theme and tooling live together under
`website/`; ignored outputs live in `website/.build/`. Dependencies stay in the
root pyproject and lock file. Run from the repository root:
`uv run --group docs python website/tools/site.py serve` to preview
and `uv run --group docs python website/tools/site.py build --strict` to build.
Run `uv run --group docs pytest website/tools` for documentation tooling changes.
Public deployment is handled by `.github/workflows/documentation.yml` after
exact-commit CI checks. Preserve the generated-only `gh-pages` history and release
immutability; do not publish raw evidence or bypass the version checks. See
`website/docs/developer/publication.md` for version rules and recovery.
Only explicitly listed examples may be copied into generated downloads. Do not
publish the AutoSuite corpus or internal refactor records. API pages use static
mkdocstrings extraction; document public APIs with English Google-style docstrings.

## 10. Compiler and reference-execution boundaries

The Python DSL (`sciloom.dsl`), shared semantic/compiler tools (`sciloom.core`)
and equipment targets (`sciloom.contrib`, or independent packages) have separate
ownership. Experiment authors import their API from `sciloom`; contributors import
`Target`, `Artifact`, `CompileResult` and `compile_ir` from `sciloom.core.compiler`.
Core must not import `sciloom.devices`, DSL, contrib or Studio; data-only
`sciloom.core.devices` binding records belong to core. The root author API stays lazy. Target
selection is explicit. Generic compilation must not import AutoSuite or assume
XML. Program/JSON v4 is the current semantic contract; see
[reference execution](docs/14_REFERENCE_EXECUTION.md). Keep vendor restrictions
(such as recursion) in target validation. The reference interpreter specifies
SciLoom behavior and is not evidence of vendor numerical or physical equivalence.

Agitation intent stays in IR; AutoSuite zone/shaker bindings belong to the target.
Declare logical dependencies with `agitator: Agitator`, independently of runtime
variables. Share existing logical references during host composition; do not
instantiate named Agitator objects or assign hardware to Function fields.
Bind deployment with `AutoSuiteTarget(devices={"agitator": AutoSuiteIndividualShaker(...)})`.
Every Target implements `resolve_devices(program) -> DeviceBindings`; empty
bindings are valid only for device-free programs. JSON v4 includes typed device
contracts, ConfigureProperty and explicit StartAgitation/StopAgitation. Set speed
with property assignment and explicitly start; no set_speed or SetAgitation alias.
Configuration captures values at assignment, and start applies the complete saved
configuration. Prove configuration across calls without assuming previous entry
invocations. Getter/augmented property access is unsupported. Native DeviceCommand
compiles via typed trusted contributor contracts; reference execution requires
defined semantics and rejects unknown native commands. DeviceIf is retained in
authored IR and selected by pure `core.specialization.specialize`. Only if/elif
accept comptime device queries. All branches are source/type checked before
selection. Target.resolve_devices sees authored IR once; validate/emit see
CompileResult.specialized_ir. The result's semantic_ir remains authored IR.
DeviceBinding includes the concrete contract and its required complete
base_contracts directory. Never import Python implementations from JSON IDs.
Backend context variables/parameters must not enter the public semantic Program. See the authoritative
[device plan](docs/refactor/device-abstraction/00-overview.md).
Consult `autosuite/docs/16_AGITATION_MAPPING.md` before changing this adapter.
Do not infer generic physical limits or hardware equivalence from one device profile.
