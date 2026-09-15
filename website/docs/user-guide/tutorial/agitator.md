# 3. Reuse a calculation

Suppose the procedure should choose a speed from the sample volume. Put the
choice in its own Function so other procedures can use it too.

`ChooseSpeed` takes `volume: Input[float]` and writes
`speed: Output[RotationalSpeed]`. Its runtime method is:

```python
if self.volume < 2.0:
    self.speed = 300 * rpm
else:
    self.speed = 600 * rpm
```

An `Output` is a result passed back to the calling Function. Assign it on
each path through the method; the `else` above supplies the result for volumes
of 2.0 or more. SciLoom Functions use output fields instead of `return`.

The volume is supplied data, in millilitres by this example's convention.
`float` itself carries no volume unit. The threshold and speeds demonstrate
a branch; they are not an experimentally established relationship.

## Use the calculation in StirRack

Replace the speed input with a volume input and a working value:

```python
volume: Input[float]
enabled: Input[bool]
shaker: Agitator
speed: Var[RotationalSpeed] = 0 * rpm
```

`Var` gives the runtime method somewhere to store a value. Unlike an input,
it is not supplied by the caller. It needs an initial value; here the calculation
will overwrite that value before it is used.

Create the child Function in a constructor:

```python
def __init__(self) -> None:
    self.choose = ChooseSpeed()
```

Python calls `__init__` when you write `StirRack()`. It runs on your computer
and creates the child instance once. Inside `run`, call it before the existing
start/stop branch:

```python
self.speed = self.choose(volume=self.volume)
```

The argument supplies the child's input. The assignment receives its output.
Keep the `if self.enabled:` branch from lesson 2; it now uses the calculated speed.

| Inputs when the generated function is called | Behaviour |
| --- | --- |
| `volume=1.5`, `enabled=True` | Start at 300 rpm |
| `volume=2.0`, `enabled=True` | Start at 600 rpm |
| `volume=1.5`, `enabled=False` | Stop; do not apply the calculated speed |

Supply both inputs even when stopping. This procedure calculates a speed before
it checks `enabled`.

## Complete file

??? example "Show choose_stirring_speed.py"

    ```python
    --8<-- "examples/tutorial/choose_stirring_speed.py"
    ```

```bash
uv run python examples/tutorial/choose_stirring_speed.py
```

```text
choose_stirring_speed.asfp
```

The package has `volume` and `enabled` inputs. Its child Function is included
in the same package.

[Python source](../../_generated/examples/tutorial/choose_stirring_speed.py) ·
[Generated package](../../_generated/examples/tutorial/choose_stirring_speed.asfp)

Next: [4. Work with a list of samples](lists-and-loops.md).
