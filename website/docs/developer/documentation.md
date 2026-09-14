# Building documentation

Use a checkout of the source repository with Python 3.14 and uv. Run these
commands from the repository root:

```bash
uv sync --locked --group docs
uv run --group docs python website/tools/site.py serve
```

Open `http://127.0.0.1:8000/`. Edit English Markdown in `website/docs/`; the server
reloads those pages. Restart preview after changing example download files so the
prepared copies are refreshed. API descriptions are extracted statically from
`src/sciloom` and `packages/sciloom-autosuite/src`, without importing device
classes or running their methods.

The website is self-contained under `website/`: `docs/` holds public pages and
assets, `theme/` holds templates, `tools/` holds build tools and their tests, and
`mkdocs.yml` configures Zensical. Internal design records stay in the repository's
separate root `docs/` directory and are not needed to build the site. The
repository is a uv workspace: dependency groups and `uv.lock` remain in the root
`pyproject.toml`, and each member under `packages/` declares only its own runtime
dependencies.

For CI-equivalent validation:

```bash
uv run --group docs python website/tools/site.py build --strict
uv run --group docs pytest website/tools
git diff --check
```

HTML is written under `website/.build/site/`. The source tree's generated downloads and
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

## Tutorial series

A tutorial series builds one program across several pages. Mark the fences that
belong to it with an HTML comment on the line before the fence; fences without a
marker are illustration and never run.

````markdown
<!-- tutorial: step -->
```python
class CountStirs(Function):
    ...
```

<!-- tutorial: checkpoint -->
```python
print(CountStirs().compile(target=AutoSuiteTarget()).write("count_stirs.asfp").name)
```
```text
count_stirs.asfp
```
````

A `step` fence is appended to the series program. A `checkpoint` runs the
program built so far plus its own optional code, and its `text` fence states the
stdout that this page adds beyond the pages before it; a checkpoint with only a
`text` fence records what the page's step itself prints. `website/tools/tutorials.py`
parses the markers, and `website/tools/handbook_test.py` registers each series
in `SERIES` with its pages in order and, optionally, the repository path of the
complete program (otherwise the last `python` fence of the last page). The tests
run every checkpoint and prove that the steps, joined, are that complete program:
a module docstring and the import layout may differ, the statements may not.

Local pages show `local` or `local-dirty` and the source SHA. PR artifacts identify
the PR head commit. [Versioned publication](publication.md) explains checked
development builds, release snapshots and deployment recovery.
