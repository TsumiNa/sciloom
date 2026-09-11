# Specify independently executable IR

## Goal

Specify independently executable IR, as specified in the [accepted plan](00-overview.md).

## Scope

Rename Package to Program, upgrade JSON to v2, separate structural schema from codec validation, publish execution semantics and implement a bounded reference interpreter with persistent function state and per-call frames.

## Non-goals

Hardware operations and numerical equivalence claims for unverified vendor edge cases.

## Acceptance

- Run shared acceptance checks in the overview on the current PR alone.
- Cover the primary behavior and rejection boundaries with colocated tests.
- Keep raw corpus evidence unchanged; compare generated outputs separately.
- Complete review, resolve feedback and confirm remote squash merge before the next PR.
