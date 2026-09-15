# 4. Work with a list of samples

For a rack of samples, supply all volumes and use the largest to choose the
speed. The new `LargestVolume` Function receives `Input[list[float]]` and
writes its answer to `largest: Output[float]`.

Its runtime method scans the supplied list:

```python
self.largest = 0.0
self.index = 0
while self.index < len(self.volumes):
    if self.volumes[self.index] > self.largest:
        self.largest = self.volumes[self.index]
    self.index += 1
```

Declare `index: Var[int] = 0` on the class. Each iteration reads one element
and advances the index. SciLoom currently supports `while` loops; it does not
yet support `for`.

Reset the index at the start of `run`, even though its declaration also says
`= 0`. A `Var` keeps its value between calls. Without this reset, the next
call would start at the end of the previous list. Reset `largest` too, so a
smaller list on the next call gets its own answer.

The initial largest value of 0.0 makes this calculation suitable for non-negative
volume data. It returns 0.0 for an empty list.

## Pass the largest value to ChooseSpeed

`StirRack` now declares `volumes: Input[list[float]]` instead of `volume`.
It creates both children in `__init__` and calls them in order:

```python
self.largest = self.measure(volumes=self.volumes)
self.speed = self.choose(volume=self.largest)
```

`self.measure` is a `LargestVolume` instance. Declare `largest: Var[float] = 0.0`
alongside the existing `speed` working value.

When AutoSuite calls this version:

| Inputs | Selected behaviour |
| --- | --- |
| `volumes=[1.0, 2.5, 0.5]`, `enabled=True` | Largest is 2.5; start at 600 rpm |
| `volumes=[1.0, 1.5]`, `enabled=True` | Largest is 1.5; start at 300 rpm |
| `volumes=[]`, `enabled=True` | Largest is 0.0; start at 300 rpm |
| `volumes=[1.0, 1.5]`, `enabled=False` | Stop |

Both inputs remain required when stopping: the volume calculation precedes the
enable/disable branch.

The empty-list behaviour is a choice in this example, not a rule that an empty
rack should be stirred. Adapt the branch to your procedure.

## List behaviour

A list has one element type, such as `list[float]`. Indexing begins at zero;
negative and out-of-range indices are errors, and assigning an element does not
extend the list.

Assigning one list field to another copies the list. A child also receives a
copy, so changing its input does not change the parent's list. The
[list scaling example](../../examples/scale-values.md) shows this with an update.

## Complete file

??? example "Show stir_sample_rack.py"

    ```python
    --8<-- "examples/tutorial/stir_sample_rack.py"
    ```

```bash
uv run python examples/tutorial/stir_sample_rack.py
```

```text
stir_sample_rack.asfp
```

[Python source](../../_generated/examples/tutorial/stir_sample_rack.py) ·
[Generated package](../../_generated/examples/tutorial/stir_sample_rack.asfp)

Next: [5. Keep a count across calls](compile.md).
