# Preserve agitation intent in domain IR

## Goal

Preserve agitation intent in domain IR, as specified in the [accepted plan](00-overview.md).

## Scope

Add logical agitator resources, typed rotational speed, set/stop operations, Python lowering and reference events/state. Existing targets explicitly reject unsupported domain operations.

## Non-goals

AutoSuite agitation emission, full unit algebra, fluid simulation.

## Acceptance

- Run shared acceptance checks in the overview on the current PR alone.
- Cover the primary behavior and rejection boundaries with colocated tests.
- Keep raw corpus evidence unchanged; compare generated outputs separately.
- Complete review, resolve feedback and confirm remote squash merge before the next PR.
