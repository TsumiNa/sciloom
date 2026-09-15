# Stir a rack of samples

This is the completed program from the [five-lesson tutorial](../user-guide/tutorial/index.md).
Use it to see how calculations and device steps fit into one procedure.

The caller supplies `volumes`, a list of sample volumes, and `enabled`,
which selects starting or stopping. The program reads those supplied numbers;
it does not measure the samples.

| Child Function | Job |
| --- | --- |
| `LargestVolume` | Find the largest supplied volume, or 0.0 for an empty list |
| `ChooseSpeed` | Choose 300 rpm below 2.0, otherwise 600 rpm |
| `CountStirs` | Count requests after the start operation completes |

With `volumes=[1.0, 2.5, 0.5]` and `enabled=True`, the procedure selects
600 rpm, saves that speed, starts the shaker and increments the counter.
With the same volumes and `enabled=False`, it stops without incrementing.
Both inputs are required on every call.

The speeds and threshold are example choices. Change `ChooseSpeed` to express
your own decision. The list loop resets its index each call, while the counter
keeps its value; [lesson 5](../user-guide/tutorial/compile.md) explains the difference.

## Compile for your rack

```bash
uv run python examples/stir_rack.py
```

```text
stir_rack.asfp
```

The package is written beside the source. Match the target's zone and shaker ID
to your AutoSuite configuration, and validate the package with AutoSuite Executor
before using it on equipment. Compiling the file does not execute the experiment.

## Source and generated package

[Download Python source](../_generated/examples/stir_rack.py) ·
[Download ASFP](../_generated/examples/stir_rack.asfp)

```python
--8<-- "examples/stir_rack.py"
```
