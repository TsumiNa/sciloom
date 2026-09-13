# Move the documentation website

## Goal

Implement the [standalone directory and command contract](00-overview.md).

## Scope

Move public content, theme, tools/tests and config together. Update Actions,
publication worktree paths, ignore rules, imports, README assets, internal links
and contributor instructions. Mark the previous site plan's layout superseded.

## Non-goals

No Python API or publishing policy changes, content redesign, dependency changes,
legacy wrappers or modifications to raw evidence and example outputs.

## Acceptance

Run the strict build and `uv run --group docs pytest website/tools`. Keep API,
snippet, download, branding, search and revision checks. The isolated publication
fixture must copy the website but not internal docs, and preserve tests for two
releases, dev updates, immutable history, exact SHA and publication boundaries.
Verify preview navigation, Mermaid and version selection. Run the existing
Python tests, mypy, AutoSuite smoke/recipe checks and examples through CI.
Run `git diff --check`; builds must not modify tracked files or recreate old
website paths. After merge verify successful Pages deployment and source metadata.
