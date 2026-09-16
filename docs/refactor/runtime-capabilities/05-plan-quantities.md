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

## Implementation

Canonical constructors and typed host arithmetic live in `sciloom.units`; root
imports expose quantities and unit aliases. Runtime unit syntax lowers to the
existing typed Literal/Binary nodes. No new record kinds or format change are
needed. Intermediate expression normalization preserves the nonnegative speed
constraint even when a temporary value is used only inside a comparison.

The [AutoSuite mapping](../../../autosuite/docs/20_QUANTITY_MAPPING.md) records
current volume/local-time evidence and a historical APP's time parameter. The
target rejects new unchecked division, speed sign and quantity-list bounds cases
until the failure gate. Reference execution supports them with explicit errors.

`examples/quantity_conversion.py` is the complete author example, with its
same-name ASFP companion. Direct IR/JSON, mypy, copy/state and read-only corpus
tests cover the stage's interfaces.

Local acceptance: 448 code/example tests, 79 website tests, mypy (72 files),
Ruff, strict website build, all 15 example commands, proposed-example syntax,
AutoSuite smoke, recipe validation and read-only corpus audit. Previous v4
golden JSON/ASFP and existing companions remain byte-identical. Remote review
and latest-head CI remain the merge gate.

## Version

Version: PATCH 0.3.1 → 0.3.2 for both workspace packages, by the user's explicit series-level version decision. JSON stays v4.
