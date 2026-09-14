# Developer Guide reference

## Goal

Make each contributor-facing fact live on exactly one Reference page, and
resolve the contradiction about required configuration.

## Scope

- `reference/architecture.md`: the package table, the layering rules, the two
  device abstractions with the class diagram from today's contributions page
  extended with `Heater`/`BenchHeater`; the node-kind sentence becomes a link;
  the analysis conventions and the flowchart move out (to Advanced in PR 10 and
  to the pipeline page here).
- `reference/pipeline.md`, retitled "Compilation pipeline": the flowchart; a
  table `Step | Function | Program it sees | Raises`; `CompileResult`; the
  canonical eight-row "Who can say no" table, whose `resolve_devices` row names
  the target's own errors and `bind_device`'s `TypeError`. The specialization
  program stays here until PR 10 moves it.
- `reference/target-contract.md`: the Target member table, `Artifact` and
  `CompileResult.write`, the minimal device-free `SummaryTarget` (executed) with
  the sentence relating it to the tutorial's `BenchTarget`, the `DeviceBinding`
  field table, the bindings rules.
- New `reference/device-contracts.md`: identity, property, command and profile
  rules; the declaration-to-IR-node table (only agitation start/stop have
  dedicated nodes); `required_configuration` stated once: `bind_device` checks
  that every required property is writable; the compiler enforces definite
  configuration only where a `StartAgitation` node requires it; a generic
  `DeviceCommand` neither requires nor supplies configuration, so a heater's
  declaration is not enforced unless its target checks it in `validate`.
- New `reference/verification.md`: the one command block, the eight example
  commands (four author, four developer), the pre-commit hook line, the
  raw-evidence paragraph. `typing-and-tests.md` and `documentation.md` shrink
  to link there.
- `reference/ir.md` and `reference/interpreter.md`: tabulated; executed first
  fences unchanged; the UUID-stability note moves to `ir.md`.
- The three old tutorials get link-only edits: their layer table and the
  sentence "checks that a lifecycle start has its required configuration on
  every reachable path" become links to the reference, so no page contradicts it.

## Non-goals

No new tutorial pages. No Advanced, FAQ or Troubleshooting pages.

## Acceptance

- `grep -n "every reachable path" website/docs` finds only
  `reference/device-contracts.md`.
- The rendered `api/compiler/` and `developer/reference/pipeline/` pages have
  different titles.
- `uv run --group docs pytest website/tools`; `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
