# Function composition

Identity copies its float input to its output. Caller creates that child in host Python, embeds the host value 2.5 and stores the call result in persistent runtime state.

## Run and inspect

```bash
uv run python examples/function_call.py
```

The source separates host specialization from execution: changing Caller(value=...) before compilation changes the embedded input. A child call binds a typed input and copies its output back on normal return. The ASFP contains both procedures; compiling the file does not execute either procedure.

The module docstring below records expected terminal output.

--8<-- "website/snippets/hardware-boundary.md"

## Source and generated files

[Download Python source](../_generated/examples/function_call.py)

- [function_call.asfp](../_generated/examples/function_call.asfp)

```python
--8<-- "examples/function_call.py"
```

