# A readable User Guide

## Goal and audience

Write for experiment authors who know Python variables, functions and if/while,
but may need a short explanation of classes, self and constructors. Keep the
handbook in English and keep Tutorial, Advanced, FAQ, Troubleshooting and Reference.
Start with an experimental task, explain the code needed for it, and show its
result. The previous counter-first tutorial and mandatory append-only user
series in the [handbook plan](../handbook-restructure/00-overview.md) are superseded.
The developer series and its cumulative execution tests remain in use.

## Decisions

- Introduce a complete fixed-speed shaker program before persistent state.
- Evolve one experiment through five independently runnable source snapshots.
  Do not force authors to append classes merely to satisfy the test harness.
- Keep existing public page URLs; change navigation titles and reading order.
- Explain class/self/__init__ only when the current example needs them. Keep
  implementation jargon, test procedures and editorial policy out of lessons.
- Explain successful programs first. Move deliberate failures to troubleshooting;
  retain the tests that exercise them. Repeat a short rule where needed instead
  of making readers follow a link for every fact.
- Use concrete language without fixed word counts, paragraph templates or an
  automated "AI writing" score. Review rendered pages as well as Markdown.
- Keep complete code tied to actual examples and long output in same-basename
  companions. Behaviour tables describe the generated procedure, not a hardware
  run. Compilation, reference execution and platform acceptance stay distinct.

Preserving the old learning order and polishing sentences alone was rejected:
authors would still encounter runtime restrictions before an experimental use.
Replacing the documentation framework was rejected: explicit page/example
mappings and the existing render tests suffice.

## Tutorial contract

| Page URL under user-guide/tutorial | New task | Source under examples/ |
| --- | --- | --- |
| first-function.md | Start a shaker at a fixed speed | tutorial/start_shaker.py |
| inputs-and-units.md | Choose speed and enable/disable at invocation | tutorial/control_shaker.py |
| agitator.md | Choose speed from a volume in a child Function | tutorial/choose_stirring_speed.py |
| lists-and-loops.md | Choose speed from a list of sample volumes | tutorial/stir_sample_rack.py |
| compile.md | Count starts and complete the program | stir_rack.py |

Every snapshot calls its entry class `StirRack` and its logical device `shaker`.
The first has no inputs and writes `300 * rpm`; the second has `speed` and
`enabled`; the third has `volume` and `enabled`; the last two have `volumes` and
`enabled`. Chapter 3 introduces Var as working storage; chapters 4 and 5 explain
resetting versus preserving it. Example speeds and thresholds are illustrative.

The initial public interface is already implemented; this example becomes a
runnable learning file in PR1. Its expected output must be obtained by running it:

```python
from pathlib import Path

from sciloom import Agitator, Function, rpm, runtime
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class StirRack(Function):
    """Start the shaker at 300 rpm.

    Attributes:
        shaker: Shaker used for the samples.
    """

    shaker: Agitator

    @runtime
    def run(self) -> None:
        self.shaker.speed = 300 * rpm
        self.shaker.start()


if __name__ == "__main__":
    target = AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
    )
    path = StirRack().compile(target=target).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
```

Command: `uv run python examples/tutorial/start_shaker.py`.
Expected stdout: `start_shaker.asfp`; complete output beside the source.
The methods do not execute during compilation; AutoSuite supplies later runtime
inputs. Ordinary Python and constructors execute on the author's computer.

## Sequence and verification

| PR | Plan | Outcome |
| --- | --- | --- |
| 1 | [First program](01-first-program.md) | This contract, writing guidance, first example and Getting started |
| 2 | [User tutorial](02-user-tutorial.md) | All five lessons and their independent examples |
| 3 | [Practical guides](03-practical-guides.md) | Four advanced pages and five author walkthroughs |
| 4 | [Reference and help](04-reference-and-help.md) | FAQ, troubleshooting, reference and consistency review |

Each stage passes review, fixes, latest checks and squash merge before the next
starts. PR2 changes the entire series atomically. Existing code checks and
examples run in each stage, plus strict site build and all website tests. Tests
compare committed companions and rendered source/downloads, and check behaviour
through the reference interpreter without presenting it as hardware evidence.

## Non-goals

No changes to shipped Python APIs, execution semantics, compiler implementation,
publication permissions, or the device/IR architecture. No invented AutoSuite UI
procedure, public package installation or instrument limits. No bulk rewrite of
the Developer Guide; only necessary links, diagnostic examples and maintenance
guidance change. Raw evidence is never modified.

## Version

Version: none, documentation, examples and verification tooling only.
