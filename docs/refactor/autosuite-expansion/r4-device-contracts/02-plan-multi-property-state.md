# R4.2: Preserve typed multi-property backend state

## Goal

Preserve typed multi-property backend state while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r4-explicit-command-effects-and-typed-configuration).
R4.1 reviewed and remotely merged.
Current code status: implemented; merged #110. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Replace the backend's single speed storage assumption with resource/property keyed typed state and call transport. Keep private symbols outside Program. Prepare direct typed profile dispatch and physical-actuator conflict checks without publishing an unnecessary one-profile protocol. Use synthetic contributor cases to verify preservation, not as native profile evidence.

Per D016, scalar allocation order stays unchanged. List properties use whole-list
capture and isolated private call arrays with normal-return copyback, separate
from ordinary public array I/O rewriting. Keep candidate wells disjoint within
one logical selection, while cross-resource collisions use physical identities.
The current typed agitation dispatch remains explicit; new lifecycle emission is
still rejected until its profile adapter is implemented with evidence.

## Non-goals

No second source of semantic configuration, family-name fake physical identities, blanket same-zone rejection for distinct real actuators, or changing existing shaker identity seeds/output.

## Acceptance

Compare existing shaker ASFP baselines byte-for-byte. Test two properties with different types, capture before later assignments, nested calls, shared/distinct resources and saved versus applied snapshots. Preserve current location gates. Test actual-identity alias rejection separately from colocated different actuators.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Implementation and local acceptance

Private DeviceStorage records retain the scalar/list property type and are keyed
by resource/property ID. Capture, transitive call dependencies, private parameter
types and copyback use that key. Scalars retain their previous allocation order.
Lists use whole-array capture, initialized private outputs and separate input/
output buffers at each call; no second public-array output buffer overwrites them.
Program/JSON remain unchanged and the typed agitation dispatch remains explicit.

Cross-resource conflicts use trusted physical identities from resolved bindings.
Within-selection ambiguity and APP well/controller ancestry still reject; distinct
actuators may share wells. Reference tests verify independent applied snapshots
for nested scopes over the same well. New native profiles and dynamic emission
remain gated; the synthetic storage harness is not a public target adapter.

Local acceptance: 1144 code/example/tool tests, 98 website tests, 48 CI example/
syntax commands, Ruff check/format, mypy (138 source files), strict docs build,
smoke and recipe checks passed. Regenerated examples leave every tracked ASFP
and JSON companion byte-for-byte unchanged. Read-only corpus audit: 271 files,
127 archive entries, 52 function XML matches, 67 templates. New focused tests
compare scalar/list saved state across nested shared and independent calls with
reference execution, including unchanged branches and repeated invocations.
Review and latest-head CI remain required; no Executor result is claimed.

## Review and completion

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: PATCH 0.7.0 → 0.7.1, fixes private typed configuration transport and
overbroad location-based conflict checks without adding a public interface,
native profile or changing existing supported output bytes. Both packages stay
lockstep; no tag or publication. Reassess after review changes.
