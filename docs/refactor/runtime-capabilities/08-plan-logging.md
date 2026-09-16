# Stage 6: Typed runtime logging

## Goal

Implement A09 as an ordered operation.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Author log call, typed IR statement, runtime scalar/quantity capture, ordered reference event and observed AutoSuite LogData task. Include category and stream expressions. Add author/developer documentation for values already supported.

## Non-goals

No telemetry, list/Zone/object formatting or application logging setup.

## Acceptance

Assert captured value/type/category/stream, source and event ordering against adjacent assignments. Compare native task shape with source evidence; distinguish logs from physical readings. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation

The root `log` author marker lowers by identity to a LogValue statement. The
typed record derives value type from its expression; labels must be text. Shared
validation, specialization, configuration analysis, reference execution and
AutoSuite generation all handle the new statement explicitly. Existing v4
records and output baselines stay unchanged.

LogEvent extends the closed event union. It retains the captured scalar or
public quantity, semantic type, labels and source. All arguments complete before
an event is appended; earlier successful events survive a later failure. Calls,
branches and loops retain ordered behavior. The existing agitation developer
example now narrows DeviceEvent explicitly before accessing its state.

AutoSuite captures all three operands into target-private variables, in the
documented value/category/stream order, then emits the observed LogData envelope.
This guarantees the manual's Macro/variable context even for constant-only logs.
Tests compare the native envelope and model generated scheduling, without
claiming Executor acceptance. Derived result types and persisted values are
tracked in RC-QA-009 and the logging evidence document.

`examples/record_values.py` and its ASFP show author usage. The developer
`examples/developer/logging_ir.py` constructs LogValue directly and writes a
same-name JSON companion before reference execution. Their actual short outputs
appear in module docstrings; public pages include/download the actual sources.

Acceptance passed: 530 code/example tests, 82 website tests including strict
builds and API/source/download checks, mypy over 78 source files, Ruff checks,
AutoSuite smoke, recipe validation, 20 CI example/syntax commands and
`git diff --check`. Read-only corpus audit passed for 271 files, 127 archive
entries, 52 function XML matches and 67 templates. Executor remains pending.

## Version

Version: PATCH 0.3.4 → 0.3.5, adding typed runtime logging under the user's
explicit lockstep 0.3.x decision. JSON stays v4.
