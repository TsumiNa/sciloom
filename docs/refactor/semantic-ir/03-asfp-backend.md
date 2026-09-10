# PR3: ASFP compilation

## Goal

Compile a Function instance into an ASFP artifact consistent with retained fixtures.

## Scope

Thin Serialization IR for AutoSuite 2.47.1.1 function XML, deterministic target IDs,
Macro ownership, field defaults and function parameter binding. Complete
`instance.compile()` with semantic IR, diagnostics, serialization IR and artifact;
provide `.write()`. Route JSON-authored IR through the same validation/backend.
Use `Test12_FIXED_CallBinding_RealInOut.asfp` as the main demonstration; add
If/Else and While fixture comparisons. Document the runnable Python example.

## Non-goals

Application generation, globals, devices, executor automation and evidence rewrites.

## Acceptance

- Demonstration emits both functions with correct input/output parameter bindings.
- Normalized comparisons preserve nesting and validate consistent ID relationships.
- If/Else and While match the corresponding confirmed fixture structures.
- Compilation is deterministic and source-instance preserving.
- New colocated pytest tests plus every preceding acceptance check pass.
- Record that actual Executor simulation requires an AutoSuite host; XML parsing
  alone must not be reported as Executor acceptance.
