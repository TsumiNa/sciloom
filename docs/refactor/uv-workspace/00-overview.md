# uv workspace and lockstep versioning

Status: implemented. The plan landed in [PR #55](https://github.com/TsumiNa/sciloom/pull/55);
the ordered PRs below merged as [PR #56](https://github.com/TsumiNa/sciloom/pull/56),
[PR #58](https://github.com/TsumiNa/sciloom/pull/58) and
[PR #59](https://github.com/TsumiNa/sciloom/pull/59). All members remain at `0.1.0`.

The AutoSuite target is the only equipment target maintained in this repository.
Before this refactor it lived inside the core distribution as
`sciloom.contrib.autosuite`. It is now its own distribution in the same
repository, the way a Cargo workspace manages several crates, so it can later
move to its own repository if its development cadence diverges from the core.
The core distribution stays dependency-free and the public documentation stays
one site.

## Decision

- The repository becomes a **uv workspace**. The root `pyproject.toml` remains
  the `sciloom` distribution and declares `[tool.uv.workspace] members = ["packages/*"]`.
- `src/sciloom/contrib/autosuite/` moves to the member
  `packages/sciloom-autosuite/src/sciloom_autosuite/`: distribution
  `sciloom-autosuite`, import name `sciloom_autosuite`. `sciloom.contrib` is
  removed; no alias remains.
- **Lockstep versions.** Every member carries the same `[project].version`, and
  one release tag `vX.Y.Z` covers the repository. The documentation build refuses
  drift. If cadences diverge later, extract the member to its own repository
  rather than adding a second version axis.
- **One documentation site** whose version axis is the lockstep version. API
  pages are extracted from both source trees; `build-info.json` keeps its four
  fields.
- The root `dev` dependency group depends on the member, so `uv sync --locked`
  installs both for development and CI; `uv sync --locked --no-dev` installs the
  core alone. The evidence corpus `autosuite/` stays at the repository root.

## Alternatives rejected

- **uv_build namespace package** (`module-name = "sciloom.contrib.autosuite"`).
  `sciloom` is a regular package whose `__init__.py` holds the lazy author
  exports, so its `__path__` is a single directory; an editable member in a
  second source tree would not be found beneath it.
- **Separate repository now.** Premature while both packages share one cadence
  and one reviewer; the workspace keeps that option open.
- **`sciloom[autosuite]` extra.** Deferred. `[project.optional-dependencies]` is
  published metadata, but `tool.uv.sources` is honoured only by uv and only for
  the project being resolved, so an outside consumer of `sciloom[autosuite]`
  would look for `sciloom-autosuite` on an index where it does not exist. A git
  URL with `#subdirectory=` hardcodes a ref, and a root -> member -> root cycle
  is undocumented in uv. When the member is resolvable from an index,
  `autosuite = ["sciloom-autosuite==X.Y.Z"]` is a one-line addition.
- **Two documentation axes** (mike `--deploy-prefix`). Two sites to maintain for
  one project.

## Consequences and non-goals

The public import path changes from `sciloom.contrib.autosuite` to
`sciloom_autosuite`; no release tag exists, so no released contract breaks.
Version bumps touch every member. Core tests that use the AutoSuite target keep
working through the `dev` group until [PR3](03-decouple-tests.md) decouples them.

Non-goals: no PyPI publication, no extra, no wheel publish job, no corpus move,
no runtime, IR or XML behaviour change, no workspace version inheritance
mechanism (uv has none).

## Interface contract

Runnable after PR1:

```python
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget, AutoSuiteVersion
```

Member `packages/sciloom-autosuite/pyproject.toml` after PR1 (no `readme`; nothing
is published):

```toml
[project]
name = "sciloom-autosuite"
version = "0.1.0"
description = "AutoSuite target for SciLoom: device profiles, deployment checks and .asfp generation."
requires-python = ">=3.12,<3.15"
dependencies = ["sciloom"]

[build-system]
requires = ["uv_build>=0.12.10,<0.13.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "sciloom_autosuite"

[tool.uv.sources]
sciloom = { workspace = true }
```

Root `pyproject.toml` additions after PR1:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
sciloom-autosuite = { workspace = true }

[dependency-groups]
dev = ["mypy>=2.3.1", "pytest>=9.1.1", "ruff>=0.16.7", "sciloom-autosuite"]

[tool.ruff]
src = [".", "src", "packages/sciloom-autosuite/src"]

[tool.mypy]
files = [
    "src/sciloom",
    "packages/sciloom-autosuite/src/sciloom_autosuite",
    "examples/function_call.py",
    "examples/agitation.py",
    "examples/scale_values.py",
    "examples/non_zero_array_min.py",
    "examples/developer",
]
mypy_path = ["$MYPY_CONFIG_FILE_DIR/src", "$MYPY_CONFIG_FILE_DIR/packages/sciloom-autosuite/src"]

[[tool.mypy.overrides]]
module = ["sciloom.core.*", "sciloom_autosuite.*"]   # strict; the relaxed test list renames its six autosuite entries
```

The member does not pin `sciloom`: lockstep is enforced by tooling and the shared
tag, and a pin would be a third place that `uv version --bump` does not update.

Enforced after PR2: `website/tools/site.py` gains

```python
def package_version(root: Path) -> str:
    """Return the version shared by the root project and every uv workspace member."""
```

which raises `ValueError("Workspace members must share the root version: ...")`
when any member under `[tool.uv.workspace].members` differs, and `source_info`
uses it. The documented bump procedure, run from the repository root:

```bash
uv version --bump <major|minor|patch>
uv version --bump <major|minor|patch> --package sciloom-autosuite
uv lock --check
uv run --group docs python website/tools/site.py build --strict
```

## Public documentation

The site is rebuilt from `main` into `dev/` after each successful push CI. PR1
updates the pages that name the import path or the packaging:
`introduction/getting-started.md`, `user-guide/compilation.md`,
`developer/compiler.md`, `api/autosuite.md`, `developer/architecture.md`,
`developer/contributions.md`, `developer/add-a-target.md`,
`developer/documentation.md`, `developer/typing-and-tests.md` and `index.md`.
PR2 updates `developer/publication.md` with the lockstep rule and the bump
procedure. PR3 changes no public page. Verify
`https://tsumina.github.io/sciloom/dev/` after each merge.

## Ordered PRs

| PR | Plan | Outcome after merge |
|---|---|---|
| 1 | [AutoSuite package](01-autosuite-package.md) | Workspace with two distributions; `sciloom_autosuite` import; all references, CI and pages updated |
| 2 | [Lockstep version](02-lockstep-version.md) | Documentation build refuses version drift; bump procedure documented |
| 3 | [Decouple tests](03-decouple-tests.md) | Core tests pass without the member; member tests import no core test module |

Each PR follows review, fixes, latest-head checks and remote squash merge before
the next starts. Later stages never begin on an unmerged predecessor. PR2 extends
the Version bump section that [PR #36](https://github.com/TsumiNa/sciloom/pull/36)
added to `branch-and-pr-workflow.instructions.md`; that rule is already on `main`.

## Version

No package version bump for this plan: documentation only. The merged state is
identified as `0.1.0+<merge commit>`.
