# Stage 17: Complete runtime workflows

## Goal

Verify the twelve additions together and teach the supported scope.

## Scope

Use [the authoritative contract](01-contract.md), not a separate API definition.
Add recipe-table, selected-shaker and per-well-label/time/CSV workflows plus the pure aspiration-chunk calculation. Pair author examples with direct IR/JSON/reference examples. Publish selected sources and same-basename outputs, update API/manual/status/Q&A and demonstrate independent Target support/rejection.

## Concrete examples and verification boundaries

- Reuse `examples/read_reagent_table.py` and its synthetic CSV for the first
  workflow: heading plus aligned experiment IDs and Volume lists. Keep its
  existing behavior and companions unchanged.
- Add `examples/stir_selected_location.py`: `shaker: Agitator`, `location:
  Input[Zone]`, `speed: Input[RotationalSpeed]`, then configuration and
  `with at(self.shaker, self.location): start(); wait(5*s); stop()`. The script
  accepts an explicit `--app` to validate a real candidate layout; without one it
  explains the input requirement. Neither path claims currently unavailable ASFP.
- Add `examples/label_sample_log.py`: trim a supplied label, read wall time once,
  form a CSV path, visit selected wells, write/read a text property and append
  one captured text record per well. Confirm before any write. No implicit
  wall clock, acknowledgement, file adapter or property service is supplied.
- Add direct typed builders for these three workflows in
  `examples/developer/runtime_workflows_ir.py`; each emits its own same-base-name
  JSON companion (`.reagent.json`, `.shaker.json`, `.labels.json`). It supplies
  deterministic reference services and demonstrates a small independent
  `ReferenceArchiveTarget` using the existing Target protocol. The target emits
  JSON for reference execution and explicitly rejects undefined native commands;
  it is not an equipment driver.
- Add `examples/aspiration_chunk.py` plus a developer reference runner: adapt
  the F31 packing loop and F30 chunk boundary arithmetic with real Volume fields.
  Preserve the 1e-12 m³ tolerance and residual/partial-fill arithmetic. Replace
  vendor global-error handling with an explicit `valid` calculation result,
  define empty/no-work outputs and prevalidate numeric inputs; do not port
  liquid-handling operations or claim equivalence of the original error handler.
  Volume-list indexing keeps this example behind the current AutoSuite guard.

The first three source/direct IR/JSON paths must have matching outputs and
ordered events. Repeated calls, empty input, cell fallback/EOF, invalid device
selection, acknowledgement failure and partial file failures must preserve the
documented state/effect rules. The aspiration adaptation is checked against
independent numeric cases and a read-only corpus formula test. Public pages
publish only these project-authored examples and their explicit companion list.

## Non-goals

No actual liquid-transfer driver, unverifiable hardware recipe, new release tag or public raw corpus.

## Acceptance

Run every new source independently, compare committed companions, Python/direct IR/JSON outputs, old v4 baselines and meaningful failure cases. Build the site, check API/search/downloads and absence of internal evidence. Separate reference/static/platform acceptance and run all shared checks.

Apply the [shared acceptance and review gate](00-overview.md#acceptance-shared-by-code-stages).
Update stage status and relevant handbook/examples when implemented. Complete
review, fixes, latest checks and squash merge before starting the next stage.
Consult [evidence](20-evidence.md) and collect new uncertainties in [Q&A](21-qa.md).

## Implementation and verification

The three combined workflows and the source-derived aspiration calculation are
implemented. Complete companions were obtained by running the examples, not by
hand-editing JSON. No ASFP is fabricated for gated workflows. The public site
includes five walkthroughs, explicit downloads, updated device/Target references
and a twelve-capability availability matrix. No runtime implementation changes
are included in this closing stage.

Local acceptance: 964 code/target/example/probe tests, 97 documentation tests,
42 CI example commands, mypy on 129 source files, Ruff check/format, strict site
build, AutoSuite smoke, recipe validation, proposed-example syntax and diff
whitespace checks pass. Corpus audit reports 271 files, 127 archive entries,
52 function matches and 67 templates unchanged. Old v4/ASFP compatibility tests
remain part of that passing suite. Browser review checked the expanded source
and visible results/downloads; rendering tests compare each new page's complete
source and published bytes against its generating file.

The real APP caught a mismatched Zone/controller name assumption; the example
now uses verified 23/22 profiles, with ancestry checked again for each supplied
layout. The finding is recorded in the selection evidence and Q&A without
changing raw data. Native failure propagation, CSV equivalence and dynamic
selection emission remain explicitly gated pending Executor results.

PR #102 review identified an oversized residual and duplicated path-normalization
logic. The calculation now rejects residuals above the original request plus
epsilon before packing; source/JSON regressions cover oversized, zero-request,
last-item and accepted-within-tolerance cases. The developer runner reuses
`repository_relative`, whose existing tests cover relative and outside-repository
paths. Companions and explanations were regenerated/updated. Version remains
none: these corrections affect examples only.

## Version

Version: none, this stage adds examples, documentation and verification rather
than shipped implementation. Both packages retain the same current 0.3.x
version (0.3.15); JSON remains v4. No release tag or PyPI publication.
