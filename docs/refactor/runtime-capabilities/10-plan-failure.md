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

## Implementation

The current macOS environment has neither AutoSuiteExecutor.exe nor Wine. The
accepted unavailable-Executor path applies: platform propagation remains
pending, and newly guarded target operations remain rejected.

`autosuite/tools/probe_runtime_failure.py` generates nine numeric-list candidate
and control ASFP/JSON pairs outside the corpus. Entry, child and loop scopes each
test an in-bounds read, upper-bound read and negative-index conversion. The
manifest records actual JSON-restored reference results, ordered markers,
node/source diagnostics, source commit/dirty status, package/target versions and
artifact hashes. Its Executor status cannot become verified through generation.
It refuses existing output directories and resolved corpus paths.

The [host procedure](../../../autosuite/docs/24_RUNTIME_FAILURE_GATE.md) requires
working controls, native bounds errors, absence of remaining markers and stopped
outer caller execution. It records re-export, APP/log hashes and configuration
separately; it does not synthesize an APP or claim platform execution.

Regression tests prove that child/loop/JSON composition cannot bypass the new
capability gate. They exposed missing function ownership in target diagnostic
paths; paths now include `$.functions[n]` while preserving node/source IDs.
No accepted v4 artifact changes and no unverified-guard override is introduced.
CI runs the colocated probe-tool tests alongside existing checks.

Acceptance passed: 565 code/example/tool tests, 82 website tests, mypy over the
82 package/example files plus a focused probe-generator type check, Ruff,
strict website build, smoke/recipe checks, 22 example/syntax commands and
`git diff --check`. The tool was actually run into a fresh scratch directory;
nine pairs and a pending manifest were inspected. Read-only corpus audit passed
for 271 files, 127 archive entries, 52 function matches and 67 templates.

## Version

Version: PATCH 0.3.6 → 0.3.7, correcting target diagnostic provenance while
establishing the explicitly pending failure gate. Both packages remain lockstep;
JSON stays v4.
