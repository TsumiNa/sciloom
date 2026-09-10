# PR2: Restricted Python lowering

## Goal

Lower a configured Function instance into validated IR without executing runtime methods.

## Scope

`Function`, `Input[T]`, `Output[T]`, scalar runtime types and `@runtime`; static
class schema registration, ordinary Python instance specialization and composed
function instances. Parse `.py` runtime source, retain source locations and lower
scalar expressions, assignment, calls, If/Else and While. Plain SciLoom annotations
declare internal fields; Python annotations remain host-time data. Expose a
Python-to-IR entry point, with the complete artifact compile API introduced in PR3.

## Non-goals

XML, Application, globals, dynamic source and unsupported runtime Python constructs.

## Acceptance

- Source/schema/specialization/type errors identify their source location.
- Different instance constants yield the expected IR without changing the instances.
- Supported control flow and composed calls lower to the same IR as JSON authoring.
- Unsupported syntax and unavailable source fail explicitly.
- New colocated pytest tests plus every PR1 acceptance check pass.
