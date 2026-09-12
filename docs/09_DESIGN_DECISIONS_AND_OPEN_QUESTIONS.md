# Design decisions and open questions

## Decisions accepted for the refactor

1. Retire handwritten ASPY as the primary user-facing representation.
2. Use a shared Typed SciLoom Semantic IR as the semantic center.
3. Build a Pydantic/SQLAlchemy-like restricted-Python DSL over that model.
4. Treat the Python DSL as a restricted source language; deliberate AST/CST lowering is part of the compiler.
5. Reuse native Python control flow where target semantics match.
6. **Class-level declarations define statically inspectable AutoSuite runtime state/schema.**
7. **The instance is the compilation unit.** `__init__` and ordinary Python provide host-time specialization/composition before compilation.
8. **Compilation is an instance method** (`instance.compile(...)`), normally provided by the AutoSuite base model; a separate top-level compile function is not the preferred public API.
9. Python is host/generation-time by default. A dedicated `@comptime` decorator is not needed in the baseline design.
10. Explicit decorators/registered special roles mark only AutoSuite runtime methods and event entry points.
11. Do not allow `__init__` to silently create new runtime state schema in the initial design; runtime fields must be class-level and registerable before instantiation.
12. Use xyflow as a graph frontend over the same IR, not as an independent compiler model.
13. Allow AI to operate on the same graph/IR or emit the same Python frontend.
14. Keep a separate Serialization IR/XML backend for AutoSuite IDs, type IDs and exact nesting.
15. Model fatal and recoverable errors separately.
16. Prefer `try/except ... raise` for structured fatal pre-stop handling rather than `except: pass`.
17. Do not use deprecated COM integration.
18. Keep ArkSuite outside the compiler's assumptions until its vendor manual/API docs are obtained.
19. Treat the AutoSuite manual as semantic documentation and the real corpus as serialization evidence; the manual does not define the `.asfp/.app` XML schema.
20. Use `Input[T]`, `Output[T]` and `Var[T]` with native Python value types. Var requires an explicit initial value; scope follows its owning model. Unwrapped annotations remain host-time data; no `Local[T]` wrapper is used.
21. Application fields will declare globals. Function `GlobalRef[T]` dependencies bind explicitly with `bind_globals(...=app.ref(...))`; Python module globals are not target globals.
22. First frontend source comes from ordinary `.py` files. Notebook, interactive and `exec()` definitions are deferred.
23. Preserve native variable initialization behavior. Reset on each invocation only through explicit runtime assignment.
24. Semantic format v2 uses explicit occurrence IDs and owned variable references; XML IDs are assigned by the backend. JSON import/export preserves IDs and semantic order.

## Important questions still open for formal refactor

- Exact Python subset accepted in runtime methods.
- Final decorator/naming scheme for runtime and application-event roles.
- Function versus Macro Task mapping in the Python object model.
- Inheritance vs composition details for Function/Macro/Application program construction.
- How constrained `for` syntax maps to repeat versus sequential/fragment execution.
- Whether fatal handler `raise` is mandatory or can be implicit after a fatal handler.
- Whether nested lexical fault regions can be lowered safely.
- Whether any local recoverable `try/except` form is worth supporting.
- Unit library/type-system implementation.
- Exact Python ↔ GUI round-trip guarantees.
- How configuration/device/zone schemas are loaded and versioned.
- Whether APP generation initially patches a known template or constructs selected application sections from scratch.
- How the Python frontend preserves semantic IDs across source edits; JSON already preserves supplied IDs.
- Source-module AST capture details for the `.py` frontend; unavailable source must produce a diagnostic.
