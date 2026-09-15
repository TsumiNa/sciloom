# Copy and scale a list

Use `ScaleValues` to multiply a list by a factor while keeping the original
values. It starts with `self.result = self.values`, which copies the whole
list, then updates each element of `result`.

Expected procedure results:

| Inputs | Output `result` |
| --- | --- |
| `values=[1.0, 2.0, 3.0]`, `factor=2.5` | `[2.5, 5.0, 7.5]` |
| `values=[]`, `factor=2.5` | `[]` |
| `values=[1.0, 2.0]`, `factor=0.0` | `[0.0, 0.0]` |

The caller's list stays unchanged. The initial whole-list assignment also
gives the output a value when the input is empty and the loop runs zero times.

`index` is a `Var`, so the method resets it before each loop. The unwrapped
`batch_size: int = 8` declaration is ordinary Python configuration and is
unused in this calculation; it does not set the list length.

## Compile the example

```bash
uv run python examples/scale_values.py
```

```text
scale_values.asfp
```

The generated function accepts `values` and `factor` on each call and returns
`result`. The Python command writes the package beside the source, without
running the calculation on equipment. The results above are covered by reference
execution; generated packages still need AutoSuite Executor validation.

For the loop syntax, see [working with samples](../user-guide/tutorial/lists-and-loops.md).

## Source and generated package

[Download Python source](../_generated/examples/scale_values.py) ·
[Download ASFP](../_generated/examples/scale_values.asfp)

```python
--8<-- "examples/scale_values.py"
```
