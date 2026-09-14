# User Guide advanced and reference

## Goal

Replace the six concept pages with Advanced pages that each open with a complete
executed program and Reference pages that hold only tables, so every author-facing
rule is stated once.

## Scope

New pages:

- `user-guide/index.md`: the overview, one paragraph per group.
- `advanced/composition.md`: executed program with a parent `StirStage` sharing
  its `shaker` slot with a child `SetSpeed` (`self.stage.shaker = self.shaker`),
  calling the child then `start()`, compiled with one binding; all of today's
  `composition.md` prose.
- `advanced/specialization.md`: executed program with constructor scalars read in
  the runtime method, two instances compiled; the `host_value` rejection; the
  host-time paragraphs of `functions.md`.
- `advanced/device-branches.md`: executed program using `comptime.can_write`,
  `comptime.supports` and `comptime.is_device`, compiled for `AutoSuiteTarget`
  and for `DemoTarget` from `examples.developer.demo_contribution`; the query
  rules from `devices.md` and the last paragraph of `control-flow.md`.
- `advanced/autosuite.md`: executed program with an explicit
  `AutoSuiteVersion.V2_47_1_1`, two shakers, and the `unsupported_short_circuit`
  rejection; "Target restrictions" from `control-flow.md`, the whole-list rule
  from `values.md`, the artifact paragraphs from `compilation.md`, "Hardware
  binding" from `devices.md`, the hardware-boundary include.
- `reference/declarations.md`, `reference/runtime-language.md`,
  `reference/devices-and-targets.md`: the tables and lists from the six pages;
  each row links to the tutorial or Advanced section that explains it.

Delete `user-guide/{functions,values,control-flow,composition,devices,compilation}.md`
and update every reference in the same PR: `website/mkdocs.yml`,
`website/docs/index.md`, `website/docs/api/index.md`, `website/docs/api/autosuite.md`,
`website/docs/introduction/getting-started.md`, the first-fence page list in
`website/tools/handbook_test.py` (remove `values` and `compilation`, add the four
Advanced pages), README (the User guide badge, the compilation link, the
"User guide" and "Devices" links), and `docs/04_PYTHON_FRONTEND_AND_STAGING.md`,
`docs/05_INSTANCE_SPECIALIZATION_AND_COMPILE_API.md`, `docs/12_PYTHON_FRONTEND.md`,
`docs/13_ASFP_COMPILER.md`, `docs/15_AGITATION_SEMANTICS.md`.

## Non-goals

No FAQ, Troubleshooting or Glossary. No Developer Guide change.

## Acceptance

- `grep -rn "user-guide/\(functions\|values\|control-flow\|composition\|devices\|compilation\)" README.md docs website .github`
  returns nothing.
- `uv run --group docs pytest website/tools`: the four Advanced programs execute.
- `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
