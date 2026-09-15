# 2. Supply a speed and switch

The first program always starts at 300 rpm. Change it so its caller can supply
a speed and choose whether to start or stop.

Add these declarations to `StirRack`, along with the existing `shaker` field:

```python
speed: Input[RotationalSpeed]
enabled: Input[bool]
```

An `Input` is a value supplied each time the generated function is called.
Here the AutoSuite caller supplies both inputs. Compiling the Python file does
not choose their values. Inputs do not have class-level defaults.

Replace the two lines in `run` with:

```python
if self.enabled:
    self.shaker.speed = self.speed
    self.shaker.start()
else:
    self.shaker.stop()
```

This is an ordinary `if/else` written inside a runtime method. When
`enabled` is false, the procedure skips the speed assignment and stops.

## What the inputs mean

The table describes what the generated function does when called:

| Inputs | Behaviour |
| --- | --- |
| `enabled=True`, `speed=300*rpm` | Save 300 rpm, then start |
| `enabled=True`, `speed=600*rpm` | Save 600 rpm, then start |
| `enabled=False`, `speed=300*rpm` | Stop and retain the previously saved configuration |

Both inputs are required on every call, including a stop request. In that branch
the supplied speed is not applied.

In Python source, write a speed with its unit, for example `300 * rpm`.
`RotationalSpeed` keeps a speed distinct from a plain number. You can also
use `rps`: `600 * rpm` and `10 * rps` represent the same speed.
The expressions in the table describe values; they are not AutoSuite UI input
instructions.

Calling `start()` again applies the newly saved speed. Setting a speed of zero
does not call `stop()`; use the explicit stop branch to disable agitation.

## Complete file

This version includes the new imports, both inputs and the unchanged equipment
binding. Use it as a replacement for the first lesson's file.

??? example "Show control_shaker.py"

    ```python
    --8<-- "examples/tutorial/control_shaker.py"
    ```

```bash
uv run python examples/tutorial/control_shaker.py
```

```text
control_shaker.asfp
```

The package is written beside its source. It now expects `speed` and `enabled`
when AutoSuite calls it.

[Python source](../../_generated/examples/tutorial/control_shaker.py) ·
[Generated package](../../_generated/examples/tutorial/control_shaker.asfp)

Next: [3. Reuse a calculation](agitator.md).
