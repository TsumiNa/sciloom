# Prepare sample labels

Use `PrepareLabels` when a later step needs a short label from supplied text.
The function removes spaces, tabs and line breaks at the ends, keeps the first
comma-separated part, and adds `_processed`.

| Input `name` | Output `label` |
| --- | --- |
| `" Sample A,extra "` | `"Sample A_processed"` |
| `""` | `"_processed"` |
| `",extra"` | `"_processed"` |

It also returns `labels=[label, "ready"]` as an independent list. These are
reference execution results. The function uses a fixed comma delimiter and index
zero, which fit the current AutoSuite text profile.

## Compile the example

```bash
uv run python examples/prepare_labels.py
```

```text
prepare_labels.asfp
```

This writes the package beside the source. The AutoSuite caller supplies `name`
when it runs the generated function. Text operations do not read a file or a
sample; they process the value that the caller provides. Generated packages still
need AutoSuite Executor validation, including the text encoding used on that host.

See [runtime text](../user-guide/reference/runtime-language.md#text) for the
supported operations and current target limits.

## Source and generated package

[Download Python source](../_generated/examples/prepare_labels.py) ·
[Download ASFP](../_generated/examples/prepare_labels.asfp)

```python
--8<-- "examples/prepare_labels.py"
```
