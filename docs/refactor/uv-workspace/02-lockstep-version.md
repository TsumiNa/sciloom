# Enforce lockstep workspace versions

## Goal

Make documentation builds refuse version drift between workspace members, and
document the bump procedure from the [contract](00-overview.md).

## Scope

Add `package_version(root)` to `website/tools/site.py` and use it in
`source_info`. Extend the `website/tools/site_test.py` fixture with a workspace
member and add a drift test. Document the procedure and the single-tag rule in
`website/docs/developer/publication.md`, the Version bump section of
`.github/instructions/branch-and-pr-workflow.instructions.md` and AGENTS.md §9.

## Non-goals

No change to `build-info.json`, `Snapshot` or `website/tools/publication.py`: a
drifted commit cannot be published, because its push CI runs the strict site
build and the snapshot worktree runs that commit's own
`site.py build --publish-ref`, which raises before recording. No version
inheritance mechanism; no bump.

## Acceptance

`uv run --group docs pytest website/tools` and the strict site build pass;
`uv version --bump patch --dry-run` and
`uv version --bump patch --package sciloom-autosuite --dry-run` print without
writing; the end-to-end publication test still produces the four-field
`build-info.json`; `git diff --check` passes. After merge,
`dev/developer/publication/` shows the lockstep rule. This PR extends the Version
bump section that [PR #36](https://github.com/TsumiNa/sciloom/pull/36) (`6a1343a`)
added to the branch workflow, so it is based on `main` at or after that commit
and after PR1 has merged.

## Version

No bump: tooling and documentation only; the merged state is
`0.1.0+<merge commit>`.
