# Building documentation

Use a checkout of the source repository with Python 3.14 and uv:

```bash
uv sync --locked --group docs
uv run --group docs python docs/tools/site.py serve
```

Open `http://127.0.0.1:8000/`. Edit English Markdown in `docs/site/`; the server
reloads those pages. Restart preview after changing example download files so the
prepared copies are refreshed. API descriptions are extracted statically from
`src/sciloom`, without importing device classes or running their methods.

For CI-equivalent validation:

```bash
uv run --group docs python docs/tools/site.py build --strict
uv run --group docs pytest docs/tools
git diff --check
```

HTML is written under `.build/docs/`. The source tree's generated downloads and
`build-info.json` are ignored. They are recreated from selected examples and the
current source revision; do not edit them. Only this public documentation tree,
selected example files and rendered API descriptions are included in the website.

API pages use mkdocstrings directives rather than handwritten signatures:

```markdown
::: sciloom.Function
    options:
      members: [compile, to_ir]
```

Use Google-style English docstrings. Explain arguments, results, errors and
execution semantics where relevant. Short example results belong in the example's
module docstring; long results belong in same-basename companion files.

Local pages show `local` or `local-dirty` and the source SHA. PR artifacts identify
the PR head commit. Automatic public deployment and release version selection are
not enabled in this foundation stage.
