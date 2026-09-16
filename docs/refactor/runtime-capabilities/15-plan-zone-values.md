# Stage 13: Runtime Zone values

## Goal

Implement the A03 value layer and a read-only layout without dynamic device actions.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add a distinct Zone type/literal, opaque well identities, ordered uniqueness, scalar fields/calls, find/combine/well_name/len, fixed reference directory and AutoSuiteLayout.from_app. Parse only verified zone/well/device relationships and enumeration order from gzip APP. Existing fixed profiles continue to compile unchanged.

## Non-goals

No list[Zone], device object as value, implicit truthiness, task/app compiler, source-corpus changes or dynamic Stir emission yet.

## Acceptance

The [stage-13 concrete contract](01-contract.md#stage-13-concrete-values-and-directory)
records the exact value, directory, environment, IR and layout interfaces before
implementation. Keep Zone distinct from scalar/list types, and preserve native
well identity independently of enumeration position. Layout parsing is read-only;
dynamic device bindings remain stage 16.

Test empty/unknown names, duplicate-combine order, well identity versus index, function passing, JSON, invalid single-well queries and layout ancestry. Corpus comparisons skip without corpus; synthetic structural tests always run. Reject unsupported target cases explicitly and run shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and verification

The stage-13 contract is implemented in core locations/IR, flow fields and zone
markers, source analysis, reference execution and the AutoSuite value adapter.
AutoSuiteLayout reads APP deployment records without mutating the corpus. It
rejects unsupported profiles and preserves well ownership and explicit ordering.
Dynamic binding remains stage 16. Zone literal output and WellName are rejected
where native representation or cardinality checks are not established.

`examples/resolve_locations.py` produces a same-name ASFP; the direct developer
example `examples/developer/zone_ir.py` produces same-name JSON and demonstrates
the fixed reference directory. Tests compare Python/IR/JSON outcomes, strict
record parsing, state/call isolation, type errors, target encodings and read-only
layout extraction. Platform behavior remains pending in the evidence matrix.

Acceptance: 820 code/example/tool tests, 92 documentation tests, 32 CI example
commands, mypy, Ruff check/format, strict website build, AutoSuite smoke, recipe
validation, corpus audit and diff whitespace checks pass. Existing canonical v4
fixtures and preexisting example artifacts are unchanged. Review and exact-head CI
must still pass before merge.

Review corrections keep Column metadata scalar-only, reconcile the earlier
directory proposal with the implemented contract, and preserve scalar/list-only
device contracts across source, direct IR, JSON and trusted bindings. They do not
change the stage's scope or version decision.

## Version

Version: PATCH 0.3.11 → 0.3.12, adding typed Zone values and read-only deployment
directories under the user's explicit lockstep 0.3.x decision. JSON remains v4;
no release tag or PyPI publication.
