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

## Implementation and verification

Every record reachable from Program now owns `__ir_kind__: ClassVar[str]`.
The structural converter discovers and validates this vocabulary through typed
dataclass fields, including types not present in an individual program. Duplicate,
missing and inherited-only identities fail as `ir_schema`; a test-only class with
a different Python name still reads and writes its original wire kind.

Expression, statement and device-predicate consumers explicitly distinguish all
current alternatives. Configuration and array-output analyses name operations
that have no effect on their facts. Unsupported native commands and unselected
branches retain explicit rejection. `assert_never` provides the type-level
completeness check; a disposable-copy mutation test removes one supported handler
from each of nine consumers and requires mypy to name the missing alternative.

Five canonical v4 fixtures were captured with the unchanged 0.2.0 implementation
at `bf7565ed2d56ca989c62647bd930eb711b457b34`, before codec edits. Their manifest
records JSON and ASFP SHA-256 hashes. Tests retain canonical JSON bytes, all ASFP
bytes (therefore UUIDs), function-call results, list copy/loop results, agitation
state and device-branch specialization. Normal example generation never updates
these fixtures. No corpus file or vendor mapping changed.

Local acceptance passed: 368 package/example tests, 79 website tests, mypy,
ruff checks/format, AutoSuite smoke, recipe validation, proposed-example syntax,
strict website build and `git diff --check`. All thirteen CI example commands
ran without changing their tracked JSON or ASFP companions. Executor behavior
is unchanged and was not tested on this host.

## Version

Version: MINOR 0.2.0 → 0.3.0 for both workspace packages, by the user's explicit 0.3.x decision; JSON remains v4.
