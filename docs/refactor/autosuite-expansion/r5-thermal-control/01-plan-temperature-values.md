# R5.1: Typed absolute temperature and rates

## Goal

Typed absolute temperature and rates while preserving the accepted semantic contract.

## Authority and dependencies

[Authoritative interface](../01-contract.md#r5-physical-temperature-and-a-fixed-thermal-family).
R4.2 merged; R5.3 additionally needs exact profile and conversion evidence or must remain gated.
Current code status: implemented; merged #111. Native status follows the [group overview](00-overview.md)
and the [evidence register](../04-evidence.md), not a successful local test.

## Implementation preflight

Perform the [mandatory reassessment](../02-execution-rules.md#mandatory-preflight):
inspect current source/callers, baseline versions, predecessor merge and new
evidence; execute or trace the planned interface examples; record the outcome
in [decisions](../05-decisions.md). For class B update contract/plans first;
for class C preserve the affected gate; for class D stop and obtain a decision.
Do not start this PR merely from a stale stage-status table.

## Scope

Implement Temperature, TemperatureDifference and TemperatureRate, canonical units and the bounded arithmetic matrix in the contract. Extend scalar/list value handling, author conversion, expression checks, JSON, snapshots and diagnostics. Every target consumer supports the exact type or rejects it explicitly.

Preflight refinement: keep absolute-unit construction literal-only, reject
thermal CSV reads until an affine conversion contract exists, and reject native
thermal values with structured diagnostics until their exact encoding is mapped.
Reference logging/append use canonical values. Test these boundaries explicitly.

## Non-goals

No vendor-specific SI offset, mass/pressure, generic dimensional algebra or native thermal profile.

## Acceptance

Test 0°C/20°C/negative Celsius, zero kelvin boundary, nonfinite/bool rejection, affine difference arithmetic, invalid absolute addition/scaling, rate/difference comparison, runtime Input/Output/Var and homogeneous lists, JSON parity and old byte baselines. Use expected numerical conventions rather than exact physical equivalence.

Run [common acceptance](../02-execution-rules.md#common-acceptance), including
new focused tests, all affected examples and old compatibility baselines.
For tools/docs-only scope use relevant tools/docs checks and read-only corpus
audit when references change. Record actual results, never predicted passes.
Update the contract's availability and group/main status table before review.

## Review and completion

Implemented affine absolute temperatures, signed differences/rates and units;
typed class/device declarations, lists, literals and operations; runtime input/
output/snapshot conversion and JSON v4 vocabulary. Source literals use 273.15.
Invalid dimensions, absolute scaling and negative absolute results reject before
later effects. Reference logging/CSV append preserve canonical values; thermal
CSV reads and AutoSuite encoding reject explicitly. No new native profile.

Author `examples/temperature_values.py` and developer
`examples/developer/temperature_ir.py/.json` are executable and included in CI.
Local acceptance after review: 1279 code/tool/example tests, 98 website tests, 50 example/
syntax commands, Ruff checks/format (307 files), mypy (139 files), strict docs,
smoke and recipe validation passed. Read-only corpus audit: 271 files, 127 archive
entries, 52 extracted function matches, 67 templates. Regenerated existing ASFP
and JSON companions are unchanged. A local test/example-generation race was
resolved by finishing generators before rerunning the complete suite; no product
change was needed. Native thermal encoding/range/profile evidence remains absent.
Review 5239643141's suppressed declaration-path comment is covered by six
property/command scalar/list contract and JSON cases; no production change.

Review, fix feedback, recheck latest head, squash merge and confirm remote MERGED
before beginning the next implementation PR. Inspect all review surfaces.
An evidence-limited implementation may be complete as implemented/gated, but its
native acceptance remains pending and compiler rejection stays enabled.

## Version

Version: MINOR 0.7.1 → 0.8.0, adds public temperature value types, units and
typed operations across source/IR/JSON/reference execution; both packages remain
lockstep. Native thermal encoding remains gated. No tag or publication.
