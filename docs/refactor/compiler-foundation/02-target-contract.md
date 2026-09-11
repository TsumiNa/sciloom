# Isolate target compilation

## Goal

Isolate target compilation, as specified in the [accepted plan](00-overview.md).

## Scope

Introduce explicit Target protocol and format-independent Artifact/CompileResult. Move AutoSuite restrictions and XML encoding validation into AutoSuiteTarget. Verify a non-XML target and backend import isolation.

## Non-goals

Interpreter and new hardware operations.

## Acceptance

- Run shared acceptance checks in the overview on the current PR alone.
- Cover the primary behavior and rejection boundaries with colocated tests.
- Keep raw corpus evidence unchanged; compare generated outputs separately.
- Complete review, resolve feedback and confirm remote squash merge before the next PR.
