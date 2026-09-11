# Validate agitation on the AutoSuite backend

## Goal

Validate agitation on the AutoSuite backend, as specified in the [accepted plan](00-overview.md).

## Scope

Bind logical agitators to explicit AutoSuite zones, map typed speed and set/stop operations using production XML evidence, and deliver a conditional agitation example with reference execution and ASFP output.

## Non-goals

Application generation, global binding, additional device families or physical simulation.

## Acceptance

- Run shared acceptance checks in the overview on the current PR alone.
- Cover the primary behavior and rejection boundaries with colocated tests.
- Keep raw corpus evidence unchanged; compare generated outputs separately.
- Complete review, resolve feedback and confirm remote squash merge before the next PR.
