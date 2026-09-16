# Stage 9: Formatted wall time

## Goal

Implement A12 as an explicit, ordered clock read.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add the contract's now_text format subset, one read per call and a controllable wall-clock environment service. Map to observed native DateTime and document platform-local versus configured reference time.

## Non-goals

No datetime values, locale/timezone formatting, unique filename guarantee or implicit host clock.

## Acceptance

Test exact fixed-clock text, format validation, separate reads across clock changes,
missing/bad services and single-read ordering across loops and child calls. The
wall service has no host-clock or elapsed-time coupling; elapsed services arrive
in stage 10. Compare native format evidence and run shared checks.

## Implementation

Implemented `now_text`, the additive v4 ReadWallTime statement, and an explicit
WallClock protocol / VirtualWallClock service. Interpreter reads once, validates
an aware datetime, writes one text destination and records an immutable
WallTimeEvent. Provider failures do not overwrite state or record a completed
read. AutoSuite emits the observed DateTime expression as one Set Variable task.

Author example: `examples/timestamp_path.py` and its generated ASFP. Developer
example: `examples/developer/wall_time_ir.py` and its JSON. Both have been run;
the latter prints `2026-09-16_140506` and one wall-time event. Dedicated tests
cover companions, direct/Python/JSON paths, schema errors, format boundaries,
clock changes, failed reads and assumed wire scheduling. See the
[mapping and remaining platform checks](../../../autosuite/docs/25_WALL_TIME_MAPPING.md).

Local acceptance passed: 610 code/example/tool tests, 82 documentation tests,
mypy (87 source files), Ruff, strict website build, 24 CI example/syntax commands,
AutoSuite smoke, recipe validation, corpus audit and diff whitespace check.
The existing v4 canonical/UUID/ASFP baselines remain unchanged. Review and
latest-head CI remain required. No Executor result is asserted.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Version

Version: PATCH 0.3.7 → 0.3.8 for ordered runtime wall-time reads, following the
user's lockstep 0.3.x decision. JSON remains v4. No release tag or PyPI publication.
