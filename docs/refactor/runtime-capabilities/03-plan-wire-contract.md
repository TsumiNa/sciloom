# Stage 1: Freeze the v4 wire contract

## Goal

Make internal Python names independent of persisted IR and detect incomplete consumers.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Declare explicit __ir_kind__ on every reachable serializable record (including nested contracts and source records). Use the typed schema to check own declarations and uniqueness. Preserve existing kinds/fields/defaults/bytes. Replace implicit remainder dispatch with explicit handling and type exhaustiveness; add meaningful node-coverage tests. Capture pre-change v4 JSON and AutoSuite artifact baselines before editing the codec.

## Non-goals

No new runtime features, format bump, migration, alternate schema, public aliases or generic plugin/pass framework.

## Acceptance

Round-trip old fixtures; compare canonical JSON and ASFP bytes/UUIDs; rename a test record while retaining its wire kind; reject missing, inherited-only and duplicate kinds and unknown JSON. Demonstrate tests fail if a supported node loses its handler. Run all shared code-stage checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: MINOR 0.2.0 → 0.3.0 for both workspace packages, by the user's explicit 0.3.x decision; JSON remains v4.

