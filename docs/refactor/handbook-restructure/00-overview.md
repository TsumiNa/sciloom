# Example-led handbooks

## Why

The public site has five sections decided by the
[documentation-site contract](../documentation-site/00-overview.md). Two of them
have not kept up with how people learn a tool. The User Guide is the six concept
pages written in PR #30 and never revised for content: about 1,850 words, two
three-line executed snippets, no complete program on any page, and an
introduction whose "first Function" shows two import lines. The Developer Guide
was strengthened in PRs #52–#54 with three step-by-step tutorials, but each
tutorial repeats the whole program (the test runs only a page's last fence, so no
page can depend on another), and the tutorials restate facts that the reference
pages also state: the two device abstractions appear on three pages, the pipeline
order on three, the `bind_device` explanation twice with an identical code block,
and one fact is contradicted (two pages say the compiler checks required
configuration for every lifecycle start; one page says, correctly, that only
agitation has such a check).

The maintainer asked on 2026-09-15 for both guides to become example-led
step-by-step tutorials, followed by advanced usage, frequently asked questions
and the rest: reference tables, a glossary and a troubleshooting page keyed by
diagnostic code.

## Decision

Re-lay both guides into the same four groups, **Tutorial**, **Advanced**, **FAQ**
and **Reference**, plus **Troubleshooting**, with one site-level **Glossary**.
Page paths change; every inbound link (README, `docs/*.md`, API pages,
navigation) is fixed in the PR that moves or removes a page.

Each guide's tutorial is one **series**: one running program built one step per
page, executed cumulatively by the documentation tests, and equal to a complete
program shown on the last page. The User Guide series builds a stirring
experiment and is committed as the runnable example `examples/stir_rack.py`. The
Developer Guide series builds a heater family, two profiles, a target and its
rejections; its complete program is the last page's fence.

Every fact is stated on exactly one page; other pages link to it. The table
[below](#ownership) names the owner of each fact that is duplicated today.

Alternatives rejected:

- Keep the existing pages and add tutorials beside them. Rejected: the overlap
  stays, the navigation grows to two parallel paths, and the contradictions are
  not resolved.
- Keep "one page, one complete program" for tutorials and chain them by prose.
  Rejected: that is what produced three independent tutorials; the repetition
  hides which line each step adds.
- Compare the series with its complete program as text. Rejected: brittle
  against import order and blank lines; the comparison is structural (AST).
- Commit the developer tutorial as a module under `examples/developer/`.
  Rejected: a second copy of about 170 lines that must stay identical to the
  fences, with a companion to regenerate on every edit; the series test already
  executes it.

Consequences: ten pull requests after this plan, all documentation and test
tooling, none touching shipped code. Two test-tooling additions (`website/tools/tutorials.py`
and its test) and one shared snippet directory `website/snippets/`. The reader
handbooks stage of the documentation-site plan is superseded by this plan for the
two guides; the examples, API and publication stages are untouched.

## Non-goals

No change to shipped code, the author API, the IR, targets or generated
artifacts. No change to the `api/` section (its pages are coupled to `__all__`
by `website/tools/api_test.py`), to `developer/brand.md`, or to the versioned
publication flow. No content from `docs/` or `autosuite/` copied to the site. No
tutorial cites `examples/proposed_frontend/`. No translation.

## Target layout

### User Guide

| Page | Title | Content |
|---|---|---|
| `user-guide/index.md` | User Guide overview | one paragraph per group; the stable link target |
| `user-guide/tutorial/index.md` | Stir a rack of samples | the story, prerequisites, the hardware-boundary note |
| `user-guide/tutorial/first-function.md` | 1. Your first Function | step `CountStirs`: `Var`, `@runtime`, host time versus runtime |
| `user-guide/tutorial/inputs-and-units.md` | 2. Inputs, outputs and speeds | step `ChooseSpeed`: `Input`/`Output`, `300 * rpm`, `if`/`else` |
| `user-guide/tutorial/lists-and-loops.md` | 3. Lists and loops | step `LargestVolume`: list input, `while` with a `Var` index, `len` |
| `user-guide/tutorial/agitator.md` | 4. Stirring with an Agitator | step `StirRack`: `shaker: Agitator`, children created in `__init__`, configure then `start()`, `stop()` |
| `user-guide/tutorial/compile.md` | 5. Bind and compile | step: the `__main__` block; the complete program included from `examples/stir_rack.py`; downloads |
| `user-guide/advanced/composition.md` | Composition and shared devices | executed program; call binding forms, frames, shared slots, configuration across calls |
| `user-guide/advanced/specialization.md` | Host-time specialization | constructor scalars become literals; the `host_value` rejection |
| `user-guide/advanced/device-branches.md` | Device-dependent branches | `comptime` rules; one program compiled for AutoSuite and for the demo target |
| `user-guide/advanced/autosuite.md` | AutoSuite rules | version, zones and ids, `and`/`or`, whole-list outputs, unused slots, artifact facts |
| `user-guide/faq.md` | FAQ | question, two-sentence answer, one link |
| `user-guide/troubleshooting.md` | Troubleshooting | reading a diagnostic; a table per phase: code, message, cause, fix, link; host-time errors |
| `user-guide/reference/declarations.md` | Declarations | field roles, runtime-method rules, inheritance, docstring convention |
| `user-guide/reference/runtime-language.md` | Runtime language | types and widening, list operations, statements and expressions, call binding |
| `user-guide/reference/devices-and-targets.md` | Devices and targets | Agitator operation table, binding names, target parameters, artifact facts, query signatures |

`introduction/getting-started.md` runs `examples/stir_rack.py` and continues to
the tutorial. `introduction/status.md` gains the long form of the hardware
boundary. The six current pages (`functions`, `values`, `control-flow`,
`composition`, `devices`, `compilation`) are removed once their content has an
owner above.

### Developer Guide

`brand.md`, `publication.md`, `documentation.md` and `typing-and-tests.md` keep
their paths in a **Project** group.

| Page | Title | Content |
|---|---|---|
| `developer/index.md` | Developer Guide overview | one paragraph per group |
| `developer/tutorial/index.md` | The heater story | the two jobs (a profile of a known family is step 2 alone; a new family is the series), class diagram, prerequisites |
| `developer/tutorial/declare-a-family.md` | 1. Declare a family | `Heater(BaseDevice)` with a `setpoint` property and `hold(seconds)`; prints the family contract |
| `developer/tutorial/declare-profiles.md` | 2. Declare profiles | `BenchHeater`, `FixedHeater` (no writable properties), a profile without capability lists is refused |
| `developer/tutorial/write-a-function.md` | 3. Write a Function against the family | `Anneal`; prints node kinds, resources and contracts of the authored program |
| `developer/tutorial/write-a-target.md` | 4. Write a target | `BenchTarget`: deployment checks, `resolve_devices` (the one `bind_device` explanation), `validate`, `emit` |
| `developer/tutorial/reject-a-program.md` | 5. Reject a program | four rejections from one program plus a deployment error; reading a diagnostic; where a check belongs; message style |
| `developer/tutorial/adapt-with-comptime.md` | 6. Adapt with comptime | `Adaptive` on both profiles; adapt instead of reject |
| `developer/tutorial/execute-what-you-can.md` | 7. Execute what you can | the interpreter refuses a native command and runs a property-only program |
| `developer/tutorial/complete-program.md` | 8. The complete program | the concatenation of steps 1–7 |
| `developer/advanced/json-interchange.md` | JSON interchange and portability | round trip, rebinding across targets |
| `developer/advanced/specialization.md` | Specialization internals | the executed program from today's compiler page |
| `developer/advanced/native-commands.md` | Native commands | what the interpreter cannot run; how AutoSuite lowers device intent |
| `developer/advanced/extending-the-analysis.md` | Extending the analysis | the recognizer and lowering conventions |
| `developer/advanced/typing-without-inheritance.md` | Typing without inheritance | structural `Target`, `TypeGuard`, what mypy does not enforce |
| `developer/faq.md` | FAQ | |
| `developer/troubleshooting.md` | Troubleshooting | one row per code, grouped by exception type |
| `developer/reference/architecture.md` | Architecture and ownership | package table, layering, the two device abstractions |
| `developer/reference/pipeline.md` | Compilation pipeline | flowchart, per-step table, `CompileResult`, the canonical rejection-layer table |
| `developer/reference/target-contract.md` | Target contract | members, artifacts, the minimal device-free target, binding fields and rules |
| `developer/reference/device-contracts.md` | Device contracts | declaration rules, declaration-to-node table, required configuration |
| `developer/reference/ir.md` | Semantic IR and JSON v4 | today's page, tabulated |
| `developer/reference/interpreter.md` | Reference execution | today's page, tabulated |
| `developer/reference/verification.md` | Verification | the command block and the example commands |

### Shared

- `website/docs/introduction/glossary.md`, with "Authoring terms" and
  "Contributor terms"; both guide overviews link to it.
- `website/snippets/hardware-boundary.md`: one admonition without links, included
  where the boundary must be visible. The directory is outside `website/docs/` so
  it is never rendered as a page; `pymdownx.snippets` resolves it from the
  repository root.
- Tutorial slugs carry no numbers; navigation titles do.

## Ownership

Each fact below is stated on its owner page; every other page links there. Two
rows name two owners on purpose: the hardware boundary has a short form (the
shared snippet) and a long form, and the agitator lifecycle has a teaching
form and a table form. Those pairs are the only allowed duplicates.

| Fact | Owner |
|---|---|
| Two device abstractions; authors subclass a family and never modify `BaseDevice` | `developer/reference/architecture.md` |
| Declaration to IR node kinds; only agitation start/stop have dedicated nodes | `developer/reference/device-contracts.md` |
| `required_configuration` is checked for writability by `bind_device` and enforced by the compiler only for `StartAgitation` | `developer/reference/device-contracts.md` |
| Pipeline order; which program each step sees | `developer/reference/pipeline.md` |
| Rejection layers, including `bind_device`'s own `TypeError` | `developer/reference/pipeline.md` |
| Empty bindings only for device-free programs; binding fields; the minimal target | `developer/reference/target-contract.md` |
| What `bind_device` returns | `developer/tutorial/write-a-target.md` |
| Compile-time query rules for authors | `user-guide/advanced/device-branches.md` |
| Adapting instead of rejecting | `developer/tutorial/adapt-with-comptime.md` |
| Verification commands and the eight example commands | `developer/reference/verification.md` |
| Compilation is not hardware acceptance | `website/snippets/hardware-boundary.md` (short), `introduction/status.md` (long) |
| Agitator lifecycle: assignment saves, `start()` applies, `stop()` is explicit, zero speed is not a stop | `user-guide/tutorial/agitator.md` (teaching), `user-guide/reference/devices-and-targets.md` (table) |
| AutoSuite target rules | `user-guide/advanced/autosuite.md` |
| Call binding forms; shared devices across calls | `user-guide/advanced/composition.md` |

## Series contract

Authoritative for PRs 1, 4 and 9. Runnable after PR 1.

Fences are marked by an HTML comment on the preceding line. A marked fence is
part of the series; an unmarked fence is illustration and is never executed.

````markdown
<!-- tutorial: step -->
```python
class CountStirs(Function):
    ...
```

<!-- tutorial: checkpoint -->
```python
print(CountStirs().compile(target=AutoSuiteTarget()).write("count_stirs.asfp").name)
```
```text
count_stirs.asfp
```
````

`website/tools/tutorials.py`:

```python
@dataclass(frozen=True)
class Block:
    kind: str             # "step" or "checkpoint"
    code: str             # empty for a text-only checkpoint
    expected: str | None  # checkpoint stdout without the trailing newline

@dataclass(frozen=True)
class Series:
    pages: tuple[str, ...]       # slugs under website/docs, in order
    complete: str | None = None  # repository-relative complete program; None means the last python fence of the last page

def blocks(markdown: str) -> list[Block]: ...
def program(root: Path, series: Series, upto: int) -> str: ...
def checkpoints(root: Path, series: Series) -> list[tuple[int, Block]]: ...
def complete_program(root: Path, series: Series) -> str: ...
def same_program(left: str, right: str) -> bool: ...
```

`program` joins the step fences of `pages[: upto + 1]`. A checkpoint on page
`p` runs `program(p) + code` after `program(p - 1)` in the same temporary
directory; its expected text is the stdout the page adds, so steps may print
(the developer series) and checkpoints may print (the user series) without
repeating earlier output. The script is named after the complete program's
basename so `Path(__file__).with_suffix(".asfp")` prints the same name the
example prints. `same_program` compares abstract syntax: a leading module
docstring is dropped, imports are compared as a set, the remaining top-level
statements as an ordered list.

`website/tools/handbook_test.py` registers:

```python
SERIES = {
    "user-guide/tutorial": tutorials.Series(
        pages=("user-guide/tutorial/first-function", "user-guide/tutorial/inputs-and-units",
               "user-guide/tutorial/lists-and-loops", "user-guide/tutorial/agitator",
               "user-guide/tutorial/compile"),
        complete="examples/stir_rack.py",
    ),
    "developer/tutorial": tutorials.Series(
        pages=("developer/tutorial/declare-a-family", ..., "developer/tutorial/complete-program"),
    ),
}
```

with `test_tutorial_checkpoint` and `test_tutorial_series_is_the_complete_program`.
`test_complete_handbook_snippet` (a page's first fence) stays for Advanced,
Reference and Troubleshooting pages; `test_complete_tutorial_snippet` is removed
when the developer series lands.

## Pull requests

| PR | Plan | Purpose |
|---|---|---|
| 1 | [Tutorial series tooling](01-tutorial-series-tooling.md) | make a multi-page series verifiable |
| 2 | [Hardware boundary snippet](02-hardware-boundary-snippet.md) | state the boundary once |
| 3 | [Stir-rack example](03-stir-rack-example.md) | add the User Guide running example |
| 4 | [User Guide tutorial](04-user-guide-tutorial.md) | the five-step series |
| 5 | [User Guide advanced and reference](05-user-guide-advanced-reference.md) | replace the six topic pages |
| 6 | [User Guide FAQ, troubleshooting and glossary](06-user-guide-faq-troubleshooting-glossary.md) | |
| 7 | [Developer Guide relayout](07-developer-relayout.md) | mechanical move into groups |
| 8 | [Developer Guide reference](08-developer-reference.md) | deduplicate the reference pages |
| 9 | [Developer Guide tutorial](09-developer-tutorial.md) | replace the three tutorials with the heater series |
| 10 | [Developer Guide advanced and FAQ](10-developer-advanced-faq.md) | |

Order: tooling before any series; the snippet before new pages include it; the
example before the series that must equal it; the User Guide before the
Developer Guide because the developer series links the User Guide's query rules;
the relayout after PR 5 has removed `user-guide/compilation.md`, so no cross-lane
link is touched; Advanced and FAQ last because they link into everything.

## GitHub Pages

After each merge `https://tsumina.github.io/sciloom/dev/` is rebuilt from
`main`; `build-info.json` records the commit. What changes on the public site:

| PR | Public change |
|---|---|
| 1 | `developer/documentation/` describes tutorial series markers |
| 2 | example pages carry the admonition; `introduction/status/` gains "What compilation establishes" |
| 3 | `examples/stir-rack/` and two downloads |
| 4 | User Guide gains the Tutorial group; getting started points at it |
| 5 | User Guide shows Tutorial, Advanced, Reference; the six old URLs disappear |
| 6 | User Guide gains FAQ and Troubleshooting; Introduction gains Glossary |
| 7 | Developer Guide shows Tutorial (old pages), Reference, Project; five old URLs disappear |
| 8 | Reference pages deduplicated; `reference/device-contracts/`, `reference/verification/` appear |
| 9 | Developer Tutorial becomes the eight-page series; three old URLs disappear |
| 10 | Developer Guide gains Advanced, FAQ, Troubleshooting |

## Version

No bump for any PR: documentation and test tooling only; shipped code is
untouched. Each PR records `Version: none, documentation and test tooling`.
