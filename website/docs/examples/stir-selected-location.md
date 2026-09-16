# Run a selected shaker for five seconds

Use a Zone input when the caller needs to choose where a step runs. This procedure
saves a speed, selects one permitted controller, starts it, waits five seconds and
stops it. The logical device is `shaker`; the location comes from the caller.

```python
@runtime
def run(self) -> None:
    self.shaker.speed = self.speed
    with at(self.shaker, self.location):
        self.shaker.start()
        wait(5 * s)
        self.shaker.stop()
```

`at()` captures and checks the location before entering its body. Leaving the
block does not stop equipment: the explicit `stop()` does. Configuring the speed
alone does not start it. The example values illustrate programming, not a recipe.

| Input | Procedure behavior |
|---|---|
| Wells on one allowed controller, 300 rpm | Run that controller at 300 rpm for five seconds, then stop |
| Empty, unknown or out-of-candidate location | Fail before starting |
| Wells spanning two controllers | Fail before starting |

The deployment declares two candidates with `AutoSuiteAgitatorSelection`. A
read-only `AutoSuiteLayout` supplies the real well-to-controller relationships.
Edit the example profiles to match your installation; a Zone name alone does
not establish its hardware identity.

```console
uv run python examples/stir_selected_location.py --app /path/to/configuration.app
```

With a valid layout and matching profiles, the script confirms the current
`unsupported_device_location` diagnostic and prints:

```text
AutoSuite dynamic ASFP emission awaits verified runtime failure propagation.
```

Without `--app`, it first prints a request for the APP path. No ASFP is produced
in either case: deployment validation works, but native selection and reliable
failure propagation still need platform verification. The
[reference workflow](runtime-workflows-ir.md) executes this procedure with two
synthetic controllers and a virtual clock; it needs no vendor files.

??? example "Complete source"

    ```python
    --8<-- "examples/stir_selected_location.py"
    ```

[Download Python](../_generated/examples/stir_selected_location.py) ·
[Location rules](../user-guide/reference/device-locations.md)
