# Getting started

Start by generating an AutoSuite function that sets a shaker to 300 rpm and
starts it. You can compile this example without a connected instrument.

## Install the checkout

You need Python 3.12–3.14, [uv](https://docs.astral.sh/uv/getting-started/installation/)
and access to the SciLoom source repository, which is currently private. There
is no public PyPI installation for this release.

```bash
git clone git@github.com:TsumiNa/sciloom.git
cd sciloom
uv sync --locked
```

This installs SciLoom and its AutoSuite target. In Python, their import names
are `sciloom` and `sciloom_autosuite`.

## Compile your first procedure

Run the supplied example from the repository root:

```bash
uv run python examples/tutorial/start_shaker.py
```

The command prints:

```text
start_shaker.asfp
```

The generated file is `examples/tutorial/start_shaker.asfp`, beside the source.
Here is the complete program:

```python
--8<-- "examples/tutorial/start_shaker.py"
```

`StirRack` describes the procedure. The two lines in `run` save a speed and then
start the shaker. `@runtime` tells SciLoom to compile those steps; it does not
run them when you execute this Python file. The code below the class constructs
the program, selects an AutoSuite target and writes the function package.

## Adapt it to your setup

Change `300 * rpm` to change the fixed speed in the generated procedure. This
value is for learning the syntax; choose experimental settings for your samples
and instrument.

`"shaker"` matches the Python field `shaker: Agitator`. The zone name
`"Heater Shaker 23"` and device ID `"23"` are example AutoSuite configuration
values. For your instrument, use the zone name and individual shaker ID from
its existing AutoSuite configuration. The ID identifies the shaker, not a vial
or rack. SciLoom does not discover those values or connect to the device.

The `.asfp` is a callable AutoSuite function package. This first function has
no inputs; its speed is fixed in the source. Generating it does not run an
experiment. Before using generated packages on equipment, validate them with
AutoSuite Executor on the deployment computer. See
[current validation limits](status.md#what-compilation-establishes).

[Download the Python file](../_generated/examples/tutorial/start_shaker.py)
or its [generated package](../_generated/examples/tutorial/start_shaker.asfp).
Continue with the [User Guide tutorial](../user-guide/tutorial/index.md) for
Function declarations, inputs and reusable steps.
