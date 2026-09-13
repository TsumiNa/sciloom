# Versioned publication

The public site is [tsumina.github.io/sciloom](https://tsumina.github.io/sciloom/).
The source repository remains private. Pages uses the current repository; changing
source visibility later does not require a new documentation address.

| Path | Source | Update policy |
|---|---|---|
| `dev/` | Checked `main` commit | Rolling development snapshot |
| `0.1.0/`, etc. | Corresponding `v0.1.0` tag | Retained release snapshot |
| `stable/` | Highest published release | Redirect alias |
| Site root | `stable/`, or `dev/` before the first release | Redirect |

Before the first release tag, publication contains only `dev`.
The package version alone does not create a release. Automatic release candidates
must match `vMAJOR.MINOR.PATCH` exactly, without leading zeroes or prerelease suffixes,
and their version must equal `[project].version` in that commit, in the root
`pyproject.toml` and in every workspace member under `packages/`. The site build
refuses a commit whose members disagree.

Each page displays the documentation version, package version and short source
SHA. Each version's `build-info.json` stores the full SHA and source ref. Source,
API, examples, build configuration and `uv.lock` all come from that same checkout.
The current publisher only assembles those completed builds into mike's history;
it never rebuilds an old release against the current source environment.

## Version bump

All workspace members carry one version. Bump every member in the same pull
request, from the repository root; each `uv version` call re-locks and syncs:

```bash
uv version --bump <major|minor|patch>
uv version --bump <major|minor|patch> --package sciloom-autosuite
uv lock --check
uv run --group docs python website/tools/site.py build --strict
```

The build fails with "Workspace members must share the root version" when a
member was missed. One `vMAJOR.MINOR.PATCH` tag then publishes the repository
release. The branch and pull request workflow instructions decide whether a
pull request bumps at all.

## Automation and permissions

PR CI builds a preview using the PR head SHA and uploads a downloadable artifact.
It has no deployment credentials. Existing Python 3.12–3.14 checks remain in CI;
documentation builds use Python 3.14.

After successful push CI, `Publish documentation` reconciles `main` and all
eligible tags. It requires a successful push CI run for each exact source SHA,
including the docs job and all three Python matrix jobs. An unfinished/failed
current main does not replace the published dev. A stale event cannot roll dev
back because selection reads current refs and checks ancestry against published
history. A moved release tag or tag/package mismatch stops publication.

The workflow runs serially. Each run checks missing tags, so replaced pending
workflow events do not lose releases. Published release directories retain their
original bytes. Stable is selected by numeric version order, not event order.
Search uses the selected version's own index.

The build job has read-only repository/Actions access. It builds each snapshot in
a separate Git worktree and locked uv environment, with GitHub tokens removed
from child build environments. A separate repository containing only generated
history is assembled locally with the pinned Zensical mike fork. Only that history
bundle and the static Pages artifact pass to the publication job.

The publication job can write `gh-pages` and deploy Pages through the
`github-pages` environment. Its Git push is not forced: concurrent external history
changes cause failure rather than being overwritten. The source checkout and its
Git history are never part of the public Pages artifact. Raw AutoSuite evidence,
internal plans and proposed examples are excluded; selected downloads are audited.

## Maintenance and recovery

Use the GitHub Actions **Publish documentation → Run workflow** action on `main`
to reconcile after a transient failure. Manual dispatch still enforces exact-SHA
CI checks and release immutability. Fix failed CI or invalid release metadata
before retrying. Do not move an already published tag or use `mike deploy` directly
to overwrite it; publish corrections under a new release tag.

If main history was intentionally rewritten behind/divergent from published dev,
publication stops for maintainer review. Do not bypass the ancestry check as a
routine recovery step. The retained `gh-pages` branch is the version history;
keep it when restoring Pages or rerunning a failed deployment.

The internal read-only preparation command is:

```bash
uv run --group docs python website/tools/publication.py --repository TsumiNa/sciloom
```

It requires a full, clean Actions checkout with fetched `origin/main`, tags and
existing `origin/gh-pages`, authenticated read access for CI lookup, and an unused
`website/.build/publication/` directory. It prepares artifacts but does not push or deploy.
Use the [local preview command](documentation.md) for ordinary documentation work.

The pinned [Zensical-compatible mike fork](https://zensical.org/docs/compatibility/mkdocs/mike/)
is transitional. Upgrade it deliberately with the release/dev history tests and
browser checks for version selection, base paths and search. Redirect aliases
avoid symlinks in Pages artifacts. No PyPI release is part of this workflow.
