# SciLoom

SciLoom — programmable scientific automation from one semantic model.

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
```

The distribution name is `SciLoom`; the Python import name is `sciloom`.

The examples show Function authoring, target configuration and `.compile()`.
They write `examples/function_call.asfp` and `examples/agitation.asfp`. Compilation does
not send commands to hardware; no knowledge of compiler internals is required.
See the [compiler guide](docs/13_ASFP_COMPILER.md) for the API and validation scope.

## AutoSuite reference materials

[`autosuite/`](autosuite/) contains original application and function exports,
matching function XML, schema samples, manual references, and supporting analysis
tools. These materials help us understand AutoSuite behavior, design the semantic
model, and validate the XML backend.

See the [reference guide](autosuite/docs/00_REFERENCE_GUIDE.md) for the collection's
organization and provenance.

## Documentation

- [Project status](docs/00_PROJECT_STATE.md)
- [Python Function frontend](docs/12_PYTHON_FRONTEND.md)
- [ASFP compilation](docs/13_ASFP_COMPILER.md)
- [Runnable function-call example](examples/function_call.py)
- [Runnable agitation example](examples/agitation.py)

## For SciLoom developers

- [Architecture and design](docs/INDEX.md)
- [Semantic IR and JSON API](docs/11_SEMANTIC_IR.md)
- [IR persistence and reference execution example](examples/developer/agitation_ir.py)
- [Proposed Python examples](examples/proposed_frontend/) — illustrative, not runnable yet.
- [Contributor and agent guidelines](AGENTS.md)
