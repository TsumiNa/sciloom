# Getting started

SciLoom currently targets Python 3.12–3.14; development is pinned to Python 3.14.
The distribution is named `SciLoom`, and the import is `sciloom`. The AutoSuite
target ships as the workspace member `sciloom-autosuite`, imported as
`sciloom_autosuite`; `uv sync --locked` installs both.

The documentation is public before the source repository. The following setup
requires repository access. A public PyPI installation is not offered by this
documentation release.

```bash
git clone git@github.com:TsumiNa/sciloom.git
cd sciloom
uv sync --locked
uv run python examples/stir_rack.py
```

The command prints `stir_rack.asfp` and writes the package beside its Python
source. It compiles the experiment; it does not run it on equipment.

## Your first Function

The [tutorial](../user-guide/tutorial/index.md) builds that program one class at
a time, from a three-line counter to the compiled package. Its declarations use
familiar Python types:

```python
from sciloom import Function, Input, Output, Var, runtime
from sciloom_autosuite import AutoSuiteTarget
```

Define a Function class in a normal `.py` file. Inputs and outputs describe values
exchanged at execution time. `Var` declares persistent internal state. Put the
experiment's assignments and control flow in one `@runtime` method, then compile
an instance with an explicit target. Host Python constructs and specializes the
instance before compilation.

Continue with [1. Your first Function](../user-guide/tutorial/first-function.md).
The rest of the [User Guide](../user-guide/index.md) states the rules the
tutorial applies.
