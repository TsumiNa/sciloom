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

## Implementation

The lazy author export `notify(message)` lowers by callable identity to Notify,
an additive v4 statement with a typed text expression. Positional and `message=`
forms work; extra/unpacked arguments and result binding are rejected. All shared
consumers explicitly handle the new node, preserving existing v4 JSON/ASFP bytes.

ReferenceEnvironment accepts an optional QueuedAcknowledgements service. It
copies and validates explicit True responses, consumes one after message
evaluation, and never prompts or confirms by default. The immutable
AcknowledgementEvent joins device and log events. Absent or exhausted responses
stop before later effects, preserving source diagnostics, earlier events and
consumed responses. Child calls and loops use the same service; explicit service
sharing shares remaining responses without merging separate environment histories.

AutoSuite first captures the text in private storage, then emits the observed
showmessage/OK task with zero timeout and no result or post-dialog pause. The
seven OK-only tasks in the primary APP supply the button policy; F21/F47 and the
representative template use different policies. This correction is recorded in
the audit and [notification mapping](../../../autosuite/docs/23_NOTIFICATION_MAPPING.md).
Executor display/blocking/continuation remains a separate pending gate.

The author example `examples/confirm_samples.py` generates its same-name ASFP.
The developer `examples/developer/confirmation_ir.py` writes/restores its JSON
companion and consumes one explicit response. Public walkthroughs, API pages,
language/execution references, download allowlist, CI and mypy are updated.

Acceptance passed: 557 code/example tests, 82 website tests, mypy over 82 files,
Ruff checks, strict website build, smoke and recipe validation, 22 CI example/
syntax commands and `git diff --check`. Corpus audit remains read-only and passed
for 271 files, 127 archive entries, 52 function matches and 67 templates.

## Version

Version: PATCH 0.3.5 → 0.3.6, adding explicit runtime acknowledgement under the
user's lockstep 0.3.x decision. JSON stays v4.
