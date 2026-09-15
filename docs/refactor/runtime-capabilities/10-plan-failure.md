# Stage 8: Runtime failure boundary

## Goal

Establish reliable AutoSuite failure propagation for newly guarded operations.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Create minimal generated probes outside the corpus, expected markers and a reference failure test. Check termination through nested functions and loops; establish diagnostic provenance. Treat checked out-of-range reads as a candidate only. Make new target capabilities needing this protection explicitly unavailable until verified.

## Non-goals

No generic Python exception handling, Application compiler, error latch/dialog masquerading as termination, or retroactive unsupported status for existing baseline programs.

## Acceptance

Record XML/re-export evidence and Executor command/version/configuration and observed results. Require the post-failure marker not to execute, including a callee failure. If Executor is unavailable, retain a documented pending gate and target rejection; do not claim platform completion. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH within lockstep 0.3.x for shipped changes, by the user's explicit series-level version decision. Choose the next patch after final review; documentation-only follow-ups use none. JSON stays v4.

