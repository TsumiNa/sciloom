# Confirm samples before continuing

Ask the operator to acknowledge a ready sample before the program records it.
Change the message in `notify()` to describe what needs checking. The sample
label comes from the caller when AutoSuite executes the generated function.

```console
uv run python examples/confirm_samples.py
```

```text
confirm_samples.asfp
```

The file appears beside the Python source. Compilation does not open a dialog.
When called with `sample="A"`, the generated function displays
“Sample A is ready. Confirm to continue.” The following log runs after OK;
there is no timeout or automatic response.

```python
--8<-- "examples/confirm_samples.py"
```

[Download Python](../_generated/examples/confirm_samples.py) ·
[Download ASFP](../_generated/examples/confirm_samples.asfp)

The OK task matches the original application and documented dialog settings.
Generated-dialog blocking and later-step execution still need Executor validation
on the AutoSuite host. See [notification rules](../user-guide/reference/runtime-language.md#request-confirmation).
