# Stage 15: Stored well metadata

## Goal

Implement A07 user text-property reads and writes.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add host WellProperty descriptor, indexed write and get with explicit optional default. Preserve high-level ordered read/write nodes, per-well reference storage and observed Get/SetProperty task mapping.

## Non-goals

No measured/configuration getter, readonly native telemetry, per-well arrays or arbitrary property types.

## Acceptance

The [concrete property contract](01-contract.md#stage-15-concrete-property-contract)
fixes the IR records, capture order, default boundary, reference store/events and
conservative AutoSuite cardinality gate before implementation. Native single-value
write mode comes from the primary APP; defaulted single-well reads come from F45/F46.

Test single-well strict read, missing/wrong-type default behavior, empty/multiwell writes, captured values and well/session isolation. Check error guarding and native property names/default fields against evidence. Run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and verification

Merged as PR #100, squash commit `e8ee675c5864da5c3dd09949c00383eddb43ea13`.
Review feedback was handled and latest-head Python 3.12–3.14/documentation CI
passed before the merge. Later status notes below record the pre-merge process.

Implemented: immutable host WellProperty declarations, additive v4 property specs
and ordered read/write nodes, explicit reference store/directory and immutable
events, typed DSL lowering, consumer coverage and AutoSuite user-property tasks.
Local fixed-point analysis proves single-well reads across branches/loops without
assuming prior calls; strict or unproven reads remain target diagnostics. The
author/direct-IR examples include generated ASFP/JSON companions. Public manuals,
API pages, download allowlist and CI examples are updated. The
[mapping note](../../../autosuite/docs/31_WELL_PROPERTY_MAPPING.md) and RC-QA-015
retain the pending Executor boundary.

Local acceptance: 898 code/example/tool tests, 92 documentation tests, mypy
(119 source files), Ruff, strict site build, smoke/recipe checks, 36 CI example
commands and corpus audit passed. The final empty-selection adapter-skip fix
also passed focused regression checks. Old v4 fixtures and pre-existing example
companions are unchanged. Remote review/CI are pending.

Copilot review on `4dd2284` completed. Its two suppressed suggestions were audited:
the reference guide count is corrected to 32 documents (00–31), and four added
regressions prove non-text property names are already rejected by the shared
dataclass structure validator before semantic validation, interpretation or
target processing. No duplicate name-type check is needed. Focused tests and
corpus audit passed; the review follow-up changes tests/docs only and retains
the version decision below. Latest-head CI remains the merge gate.

## Version

Version: PATCH 0.3.13 → 0.3.14 in both workspace packages, adding stored well text
properties under the user's explicit lockstep 0.3.x decision. JSON remains v4;
no release tag, migration or PyPI publication.
