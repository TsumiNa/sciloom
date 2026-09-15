# Stage 3: Volume and duration

## Goal

Implement A02 as finite, explicit physical types.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Volume/Duration author values and units, canonical SI storage, scalar/list types, static/runtime unit construction and the agreed arithmetic. Support conversion in type checking, reference values, JSON and AutoSuite variable/parameter encoding; preserve RotationalSpeed.

## Non-goals

No arbitrary dimensional system, temperature offsets, device limits or duration-as-auto-stop.

## Acceptance

Test mL/uL/L and s/minute/hour conversion, signed differences, ratios, runtime multiplication, lists, finite/bool rejection and incompatible dimensions. Compare original volume parameters and initial values; record numerical evidence limits. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

