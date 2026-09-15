# Call another Function

Use a child Function when several procedures need the same calculation.
This small example copies a value so you can see the input and output passing
without additional experimental logic.

`Caller` creates an `Identity` child in its constructor. Its runtime method
calls the child with `x=self.value` and stores the returned `y` in
`self.result`. With the default constructor argument, that value is 2.5.

To use another fixed value, construct `Caller(value=7.0)` before compiling.
The generated package contains both Functions. `result` is internal
`Var` state; it is not an output parameter of `Caller`.

## Compile the example

```bash
uv run python examples/function_call.py
```

```text
function_call.asfp
```

The package is written beside the source. This command compiles the two
Functions; it does not execute the copy. See
[reusing a calculation](../user-guide/tutorial/agitator.md) for the same pattern
in the stirring procedure.

## Source and generated package

[Download Python source](../_generated/examples/function_call.py) ·
[Download ASFP](../_generated/examples/function_call.asfp)

```python
--8<-- "examples/function_call.py"
```
