# Stage 16: Runtime device locations

## Goal

Complete A03 through explicit selection scopes and trusted candidates.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Implement at, immutable common-contract candidate profiles, data-only selection bindings and APP-based allowed-well/controller checks. Extend scope/configuration analysis, specialized traversal and inherited shared-device context. Track saved logical config separately from applied/enabled physical state; add physical result snapshots. Native backend context transport remains gated as described below.

The [concrete selection contract](01-contract.md#stage-16-concrete-selection-contract)
records exact binding/IR/environment/snapshot interfaces before implementation.
The stage-8 evidence gate currently prevents safe AutoSuite dynamic emission:
candidate/layout validation is implemented, while DeviceAt/candidate compilation
must fail explicitly. Private native selection transport cannot be activated until
failure propagation is verified; do not add an unchecked bypass or unused emitter.

## Non-goals

No arbitrary unbounded hardware selection, overlapping logical candidate sets, implicit stop/restore, same-device nested selection or model-bound hardware objects.

## Acceptance

Test fixed bindings unchanged; missing/wrong/duplicate candidates; empty, outside and multicontroller zones; value capture; scope inheritance and same-device nesting. Test A-to-B selection leaving A running, stops per controller, cross-function configuration and immutable physical snapshots. Prove runtime rejection before body effects; run shared checks and record Executor status.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and validation

Merged as PR #101, commit `aa75dce16e94384e2bfeaa167cd82dc2bb98ab43`, after
Copilot review (no code comments/threads), all review surfaces checked and
Python 3.12–3.14/documentation CI passed. The following records pre-merge checks.

Implementation is ready for review: Python/direct IR/JSON, captured scopes,
transitive call checks, physical snapshots and APP ancestry validation are
covered. The developer example prints A running at 300 rpm and B stopped with
600 rpm last applied; its complete v4 companion is committed. The AutoSuite
failure gate is explicit and has no bypass. Review and latest CI remain required
before merge and stage 17.

Validation: 932 core/target/example/tool tests (931 full-suite cases plus the
new direct-IR companion/rebinding case), mypy (124 files), Ruff, strict website
build, all 92 website tests (the download-path failure was fixed and the two
rendering tests rerun), 37 CI example commands, smoke, recipe, proposed-source
syntax and corpus audit pass. Existing companions and v4 baselines are unchanged.
Corpus audit reports 271 files, 127 archive entries, 52 function matches and
67 templates for this local checkout. Executor is unavailable.

## Version

Version: PATCH 0.3.14 → 0.3.15 in both workspace packages, implementing bounded
runtime device locations under the user's explicit lockstep 0.3.x decision.
JSON remains v4; old canonical documents and fixed-device output are unchanged.
No release tag or PyPI publication.
