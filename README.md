# SciLoom

SciLoom — programmable scientific automation from one semantic model.

SciLoom aims to let scientists and engineers author automation workflows through
Python, a visual editor, and AI tools, all sharing one typed semantic model.
AutoSuite is the initial target for compilation.

The project is in its design and scaffolding stage. The compiler and authoring
interfaces are not implemented yet.

## Getting started

Use Python >=3.12,<3.15 and uv. The development environment is pinned to Python 3.14.

```bash
uv sync --locked
uv run python -c "import sciloom"
```

The distribution name is `SciLoom`; the Python import name is `sciloom`.

## AutoSuite reference materials

[`autosuite/`](autosuite/) contains original application and function exports,
matching function XML, schema samples, manual references, and supporting analysis
tools. These materials help us understand AutoSuite behavior, design the semantic
model, and validate the future XML backend.

See the [reference guide](autosuite/docs/00_REFERENCE_GUIDE.md) for the collection's
organization and provenance.

## Documentation

- [Project status](docs/00_PROJECT_STATE.md)
- [Architecture and design](docs/INDEX.md)
- [Proposed Python examples](examples/proposed_frontend/) — illustrative, not runnable yet.
- [Contributor and agent guidelines](AGENTS.md)
