# Explicit device lifecycle effects

Extend `Agitator` with a typed gain property and explicit apply/disable commands.
An independent recording target binds a concrete profile; no device family or
compiler subclass needs modification.

```bash
uv run python -m examples.developer.lifecycle_commands
```

The first apply uses the gain captured before the local variable changed. The
second apply uses the updated configuration. A later write changes saved gain to
3.0 without changing applied gain 2.0; disabling retains both snapshots. JSON v4
round-trips the new command contracts. The module docstring records the output.

These are reference effects. AutoSuite reports `unsupported_device_command`
until a verified typed profile adapter exists; recording JSON does not execute
equipment. Ordinary commands without defined effects remain unsupported by the
reference interpreter.

## Source and generated files

[Download Python source](../_generated/examples/developer/lifecycle_commands.py)

- [lifecycle_commands.json](../_generated/examples/developer/lifecycle_commands.json)

```python
--8<-- "examples/developer/lifecycle_commands.py"
```
