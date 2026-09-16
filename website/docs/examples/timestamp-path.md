# Put a timestamp in a filename

Build a result filename when AutoSuite calls your function. The caller supplies
the directory text. `now_text()` captures the time once; the next assignment
joins that text into a path.

```console
uv run python examples/timestamp_path.py
```

```text
timestamp_path.asfp
```

The generated package appears beside the Python file. With `directory="results"`
and local time 2026-09-16 14:05:06, its outputs are:

| Output | Value |
| --- | --- |
| `stamp` | `2026-09-16_140506` |
| `path` | `results/2026-09-16_140506.csv` |

This constructs a name; it does not create the file or directory. Calls in the
same second can produce the same name. Change the format in `now_text()` to
change the displayed fields, using the [supported directives](../user-guide/reference/runtime-language.md#read-wall-time).

```python
--8<-- "examples/timestamp_path.py"
```

[Download Python](../_generated/examples/timestamp_path.py) ·
[Download ASFP](../_generated/examples/timestamp_path.asfp)

AutoSuite uses its host's local time, including daylight-saving rules. The
mapping matches the original timestamp function; Executor verification of the
generated package, formatting and boundary behavior is still pending.
