# SciLoom

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="website/docs/assets/brand/svg/sciloom-banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="website/docs/assets/brand/svg/sciloom-banner-light.svg">
  <img src="website/docs/assets/brand/svg/sciloom-banner-light.svg" alt="SciLoom — programmable scientific automation" width="1800">
</picture>

SciLoom — programmable scientific automation from one semantic model.

[Documentation](https://tsumina.github.io/sciloom/) ·
[User guide](https://tsumina.github.io/sciloom/dev/user-guide/) ·
[API reference](https://tsumina.github.io/sciloom/dev/api/)

SciLoom aims to let scientists and engineers author automation workflows through
Python, a visual editor, and AI tools, all sharing one typed semantic model.
AutoSuite is the initial target for compilation.

Write reusable Python Functions, compose them and compile them to AutoSuite
function packages. Conditional agitation is the first experimental operation.
Application generation and broader device support remain under development.

## Getting started

Use Python >=3.12,<3.15 and uv. The development environment is pinned to Python 3.14.

```bash
uv sync --locked
uv run python -c "import sciloom"
uv run python examples/function_call.py
uv run python examples/agitation.py
uv run python examples/scale_values.py
uv run python examples/non_zero_array_min.py
uv run python examples/stir_rack.py
```

The distribution name is `SciLoom`; the Python import name is `sciloom`. The
repository is a uv workspace: `uv sync --locked` also installs the AutoSuite target
member `sciloom-autosuite` from `packages/`, imported as `sciloom_autosuite`.

The examples show Function authoring, target configuration and `.compile()`.
They write `examples/function_call.asfp` and `examples/agitation.asfp`. Compilation does
not send commands to hardware; no knowledge of compiler internals is required.
See the [tutorial](website/docs/user-guide/tutorial/index.md) for usage and the
[AutoSuite rules](website/docs/user-guide/advanced/autosuite.md) for validation scope.

## AutoSuite reference materials

[`autosuite/`](autosuite/) contains original application and function exports,
matching function XML, schema samples, manual references, and supporting analysis
tools. These materials help us understand AutoSuite behavior, design the semantic
model, and validate the XML backend.

See the [reference guide](autosuite/docs/00_REFERENCE_GUIDE.md) for the collection's
organization and provenance.

## Documentation

- [English handbook](website/docs/index.md)
- [Brand assets and usage](website/docs/developer/brand.md)
- [Getting started](website/docs/introduction/getting-started.md)
- [User guide](website/docs/user-guide/index.md)
- [Devices and targets](website/docs/user-guide/reference/devices-and-targets.md)
- [Example walkthroughs](website/docs/examples/index.md)
- [Runnable function-call example](examples/function_call.py)
- [Runnable agitation example](examples/agitation.py)
- [List copying and scaling](examples/scale_values.py)
- [Numeric Non Zero Array Min](examples/non_zero_array_min.py)
- [The tutorial's stirring program](examples/stir_rack.py)

## For SciLoom developers

- [Architecture and design](docs/INDEX.md)
- [Developer handbook](website/docs/developer/index.md)
- [IR persistence and reference execution example](examples/developer/agitation_ir.py)
- [Proposed Python examples](examples/proposed_frontend/) — illustrative, not runnable yet.
- [Contributor and agent guidelines](AGENTS.md)
