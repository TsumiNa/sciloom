# 5. Keep a count across calls

Add a counter to record how many times the procedure requests a start.
Unlike the loop index, this value should keep increasing between calls.

```python
class CountStirs(Function):
    """Count start requests.

    Attributes:
        stirs: Number of starts requested in this session.
    """

    stirs: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.stirs += 1
```

There is no reset in `run`. The initial zero is used when runtime state is
first created; later calls continue from the saved value.

Create `self.counter = CountStirs()` in `StirRack.__init__`, then call
`self.counter()` immediately after `self.shaker.start()`. This child has no
inputs or outputs, so the call needs no arguments or assignment.

## Decide which values to keep

The generated procedure retains the counter while the same runtime state is
in use. A new reference-execution session starts fresh; retention after an
AutoSuite application restart or fault recovery is not established.

| Successive calls using the same state | Counter |
| --- | --- |
| Start with `enabled=True` | 1 |
| Start again with `enabled=True` | 2 |
| Stop with `enabled=False` | Still 2 |

This counts completed start requests in the procedure, not measured motion.
Two separately created `CountStirs()` instances have independent counters.
The same child instance called twice uses the same counter.

The loop index from lesson 4 is also a `Var`, but it is explicitly reset at
the start of each call. Choose where to reset a value based on what your
procedure needs to remember.

## The complete procedure

This file combines the volume calculation, speed choice, start/stop branch
and counter. The caller still supplies only `volumes` and `enabled`.

??? example "Show stir_rack.py"

    ```python
    --8<-- "examples/stir_rack.py"
    ```

```bash
uv run python examples/stir_rack.py
```

```text
stir_rack.asfp
```

The package is written beside the source. The Python command compiles it;
AutoSuite calls the generated function with the input values. Before using it
on equipment, check the binding against the installed configuration and
validate the package with AutoSuite Executor on the deployment computer.

[Python source](../../_generated/examples/stir_rack.py) ·
[Generated package](../../_generated/examples/stir_rack.asfp)

To reuse device operations across procedures, continue with
[composition and shared devices](../advanced/composition.md). For the complete
language rules, see [runtime syntax](../reference/runtime-language.md).
