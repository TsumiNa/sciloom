# User Guide tutorial

## Goal

Teach an experiment author, from nothing to a compiled `.asfp`, through one
stirring program built one step per page and verified by the series test.

## Scope

Pages under `website/docs/user-guide/tutorial/`, each with one `step` fence and
one or more `checkpoint` fences per the [series contract](00-overview.md#series-contract):

| Page | Step | Checkpoints |
|---|---|---|
| `index.md` | none | none; the story, prerequisites, the hardware-boundary include |
| `first-function.md` | `CountStirs` | compile to `count_stirs.asfp`; reading `CountStirs().stirs` from host Python is refused (`runtime_field_read`) |
| `inputs-and-units.md` | `ChooseSpeed` | `600 * rpm == 10 * rps`; compile; assigning a bare number to a speed output is refused (`type_mismatch`) |
| `lists-and-loops.md` | `LargestVolume` | compile; a `for` loop is refused (`python_subset`) |
| `agitator.md` | `StirRack` | compiling with `AutoSuiteTarget()` fails with `missing_resource_binding`, which motivates the next page |
| `compile.md` | the `__main__` block | text-only: the program prints `stir_rack.asfp`; then "The complete program" includes `examples/stir_rack.py` and links the downloads |

Prose moves from the current pages in teaching form: `functions.md` "Host time
and runtime" and "State and repeated calls" to page 1; `values.md` "Rotational
speed" to page 2 and "Lists are values" to page 3; `devices.md` introduction and
lifecycle prose to page 4; `compilation.md` first two paragraphs to page 5. The
rule tables stay where they are until PR 5 moves them to Reference.

Register the series in `website/tools/handbook_test.py` (`SERIES["user-guide/tutorial"]`
with `complete="examples/stir_rack.py"`) and add the walkthrough row
`("user-guide/tutorial/compile", "stir_rack")`. Add the Tutorial group to the
User Guide nav in `website/mkdocs.yml`, keeping the six existing entries.
`website/docs/introduction/getting-started.md` runs `examples/stir_rack.py` and
continues to the tutorial.

Expected `text` fences are captured from real runs, never typed by hand.

## Non-goals

No page removed. No Advanced, FAQ or Reference pages.

## Acceptance

- `uv run --group docs pytest website/tools`: every checkpoint passes and the
  series equals `examples/stir_rack.py`.
- `uv run --group docs python website/tools/site.py build --strict`; the new
  pages are reachable from the nav and from getting started.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
