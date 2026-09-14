# 5. Bind and compile

The program names a logical `shaker`. The target maps that name to one real
instrument, then compiles.

<!-- tutorial: step -->
```python
from pathlib import Path

from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget

if __name__ == "__main__":
    target = AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")},
    )
    path = StirRack().compile(target=target).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
```

`AutoSuiteIndividualShaker` is a **profile**: deployment data for one individual
shaker, its AutoSuite zone name and its device id. A profile describes where the
program will run; it opens no connection. The `devices` mapping is keyed by the
field name the program used, `shaker`; every declared device needs an entry, even
one the method never touches.

`compile` checks the program once more against the bound instrument, then hands
the artifact back; `write` puts it on disk and returns the path. The `.asfp`
file is the whole package: a callable procedure whose inputs, `volumes` and
`enabled`, are supplied when AutoSuite runs it.

<!-- tutorial: checkpoint -->
```text
stir_rack.asfp
```

--8<-- "website/snippets/hardware-boundary.md"

## The complete program

The five steps, in order, are this file. It is the
[stir-rack example](../../examples/stir-rack.md), which the repository runs on
every change so the package stays reproducible.

```python
--8<-- "examples/stir_rack.py"
```

[Download Python source](../../_generated/examples/stir_rack.py) and the
generated [stir_rack.asfp](../../_generated/examples/stir_rack.asfp).

Where next: the [Advanced pages](../index.md) each open with a program that
goes one step beyond this one, the [Reference](../reference/declarations.md)
states the rules the tutorial applied, and the
[agitation example](../../examples/agitation.md) is the smallest device program.
