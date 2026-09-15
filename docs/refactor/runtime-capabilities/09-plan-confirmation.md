# Stage 7: Explicit acknowledgement

## Goal

Implement A10's text message and OK-only blocking contract.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Author notify, IR semantics, an explicitly configured reference acknowledgement source and observed showmessage/OK task. Missing reference response raises instead of allowing the next statement.

## Non-goals

No input value, cancel recovery, timeout choice, automatic default response or production hardware UI implementation.

## Acceptance

Test text evaluated once, the next effect only after acknowledgement and missing-response failure. Compare dialog mode/fields with original evidence and record Executor acceptance separately. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

