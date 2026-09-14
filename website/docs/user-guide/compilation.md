# Compiling a program

Construct a Function instance, choose the target explicitly, and write the result.
For the repository's device-free scaling example:

```python
from examples.scale_values import ScaleValues
from sciloom_autosuite import AutoSuiteTarget

compiled = ScaleValues().compile(target=AutoSuiteTarget())
compiled.write("scale_values.asfp")
```

The generated artifact contains a callable procedure with runtime inputs; compilation
does not supply those inputs or run the experiment. The return value of `write`
is the destination Path. Parent directories are created when needed, and an
existing destination is overwritten. Target selection never happens implicitly.

AutoSuite currently targets version 2.47.1.1 and emits UTF-8 XML with media type
`application/xml` and suffix `.asfp`. Device profiles select concrete shaker and
zone bindings. See [Devices](devices.md) for the configuration lifecycle.

## Diagnostics

Invalid declarations may fail when the Function class is created. Source, semantic
and target checks run during compilation. Errors retain diagnostics with a code,
message, semantic path and source location when available. Fix the originating
declaration or runtime operation rather than editing generated XML.

Typical failures include unsupported Python syntax, mismatched types, missing
call bindings, unconfigured starts, unsupported selected operations, recursion,
and AutoSuite list outputs that are not initialized on every path.

The AutoSuite adapter uses internal storage for saved device configuration and
isolates list parameters to preserve value-copy semantics. These details do not
change the experiment's public input/output signature.

## What validation establishes

--8<-- "website/snippets/hardware-boundary.md"

[Current capabilities](../introduction/status.md#what-compilation-establishes)
states what still requires validation on the platform.

Developers can inspect the authored and selected IR using the
[compiler contract](../developer/compiler.md).
