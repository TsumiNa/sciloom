# Developer Guide tutorial

## Goal

Replace the three independent tutorials with one eight-page series that builds a
heater family, two profiles, a target and its rejections, executed cumulatively.

## Scope

Pages under `website/docs/developer/tutorial/`, each of 1–7 with exactly one
`step` fence and a text-only `checkpoint` for what the step prints; page 8 holds
the complete program (the series is registered with `complete=None`):

| Page | Step | Prints |
|---|---|---|
| `index.md` | none | the two jobs, class diagram, prerequisites |
| `declare-a-family.md` | all imports; `Heater(BaseDevice)` with `setpoint` and `hold(seconds)`; `device_contract(Heater)` | family id, base, properties, commands |
| `declare-profiles.md` | `BenchHeater`, `FixedHeater` (no writable properties); `LazyHeater` without lists inside `try` | `bind_device` read-back for both; the refusal message |
| `write-a-function.md` | `Anneal(Function)`; `Anneal().to_ir()` | node kinds, resources, contracts (the family, no target) |
| `write-a-target.md` | `BenchTarget` with `__init__` checks, `resolve_devices`, `validate`, `emit`; compile `Anneal` | pipeline order, target id and media type, selected contracts (the profile) |
| `reject-a-program.md` | `report`, `RuntimeHold`, the four `try` blocks, the deployment error | the five reports |
| `adapt-with-comptime.md` | `Adaptive` using `comptime.can_write`; compiled on both profiles | selected node kinds per profile |
| `execute-what-you-can.md` | `Interpreter` on `Anneal` (refused) and on `Preheat` (runs) | the refusal code and message; `True {'setpoint': 60.0}` |
| `complete-program.md` | none; one complete fence | |

Prose kept from the old pages: family versus profile (index), "Reading a
diagnostic", "Where your own check belongs", "Writing a rejection the author can
act on" (page 5), "adapt instead of reject" (page 6). Prose linked instead of
repeated: the pipeline, the rejection layers, bindings rules, required
configuration (reference pages); the query rules (User Guide Advanced). Page 4
keeps a short typing note and page 7 a short native-command note until PR 10.

Delete `developer/add-a-device.md`, `add-a-target.md`, `reject-a-program.md`
and `test_complete_tutorial_snippet`; register `SERIES["developer/tutorial"]`;
update the nav and every link from `reference/*`, `developer/index.md`,
`examples/demo-device.md` and `api/devices.md`. Expected `text` fences are
captured from real runs.

## Non-goals

No Advanced, FAQ or Troubleshooting pages. No committed example module for the
series.

## Acceptance

- `uv run --group docs pytest website/tools`: every checkpoint passes and the
  series equals page 8.
- `grep -rn "add-a-device\|add-a-target\|reject-a-program" README.md docs website .github`
  returns only `docs/refactor/` history.
- `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
