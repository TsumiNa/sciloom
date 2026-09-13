# CLAUDE.md

Claude Code entry point for this repository.

## Read this first

[`AGENTS.md`](AGENTS.md) is the authoritative instruction file for this package.
Read it in full before starting work. This file only routes to it and records
Claude Code specifics; it does not restate or override it. If the two ever
disagree, `AGENTS.md` wins.

## Claude Code specifics

- Claude Code does not load the instruction files under
  [`.github/instructions/`](.github/instructions/) automatically. `AGENTS.md`
  requires them: read every applicable file yourself, using its `applyTo` and
  `description` to decide scope, and recheck when the task expands to new files
  or activities.
- The default interactive shell here is `fish`. Confirm the shell your tool
  actually runs before relying on heredocs, and prefer the Write and Edit tools
  over shell redirection for file content.
- Run project commands through `uv run ...`; the required checks are listed in
  `AGENTS.md` §8.
