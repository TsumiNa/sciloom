# Getting started

SciLoom currently targets Python 3.12–3.14; development is pinned to Python 3.14.
The distribution is named `SciLoom`, and the import is `sciloom`.

The documentation is public before the source repository. The following setup
requires repository access. A public PyPI installation is not offered by this
documentation release.

```bash
git clone git@github.com:TsumiNa/sciloom.git
cd sciloom
uv sync --locked
uv run python examples/scale_values.py
```

The command prints `scale_values.asfp` and writes the package beside its Python
source. It compiles the experiment; it does not run it on equipment.

## Your first Function

The [ScaleValues example](../examples/scale-values.md) copies a list and scales
its elements. Its declarations use familiar Python types:

```python
from sciloom import Function, Input, Output, Var, runtime
from sciloom.contrib.autosuite import AutoSuiteTarget
```

Define a Function class in a normal `.py` file. Inputs and outputs describe values
exchanged at execution time. `Var` declares persistent internal state. Put the
experiment's assignments and control flow in one `@runtime` method, then compile
an instance with an explicit target. Host Python constructs and specializes the
instance before compilation.

Read [Functions and fields](../user-guide/functions.md) next. For equipment
operations, continue with [Devices](../user-guide/devices.md) and the
[agitation walkthrough](../examples/agitation.md).
