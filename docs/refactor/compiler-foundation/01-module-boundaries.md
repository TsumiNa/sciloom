# Organize compiler module boundaries

## Goal

Organize compiler module boundaries, as specified in the [accepted plan](00-overview.md).

## Scope

Move Python model/lowering into frontends/python and ASFP/XML code into backends/autosuite. Update imports, colocated tests and documentation paths without behavior changes.

## Non-goals

Target API or IR semantic changes.

## Acceptance

- Run shared acceptance checks in the overview on the current PR alone.
- Cover the primary behavior and rejection boundaries with colocated tests.
- Keep raw corpus evidence unchanged; compare generated outputs separately.
- Complete review, resolve feedback and confirm remote squash merge before the next PR.
