# Stage 0: Record the accepted contract

## Goal

Record the durable IR rules and all twelve bounded interfaces before implementation.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
The overview, authoritative contract, per-stage plans, evidence matrix, collected Q&A and project/instruction links. Mark all new runtime APIs pending; link the merged audit and preserve historical migrations.

## Non-goals

No shipped-code changes, new runtime nodes, version bump or corpus writes.

## Acceptance

Check all local links, all stage links and Version sections, the complete A01–A12 mapping, and consistency with the accepted user plan. Run strict site build, all website tests and git diff --check; ensure internal plans are absent from public output.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: none, plans and instructions only.

