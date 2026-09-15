# Stage 4: Bounded numeric operations

## Goal

Implement A11 with explicit Python-compatible result semantics.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Resolve abs, math.floor and one-argument round; type and execute numeric unary operations. Convert quantities explicitly before rounding. Provide supported AutoSuite mapping or diagnostics when equivalence/range is unproven.

## Non-goals

No ndigits, full math module, random operations or inferred machine integer width.

## Acceptance

Test positive/negative boundaries, exact half ties, large/range-limited values, nonfinite inputs and quantity type rules. Test unsupported target ranges; never assume native round implements ties-to-even. Preserve prior behavior and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

