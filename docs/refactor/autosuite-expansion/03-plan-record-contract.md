# R0: Record the accepted expansion contract

## Goal

Make the seven-refactor sequence reviewable before production changes.

## Scope

The [contract](01-contract.md), ordered subplans, baseline evidence, explicit
API availability, preflight/stop rules, Q&A, decisions and docs index link.
Add a discoverable pointer in AGENTS.md so later implementers read these rules.
No previous plan is silently rewritten as a new implementation claim.

## Non-goals

No production code, dependency/version changes, corpus writes, generated device
artifacts or native capability unlock.

## Implementation preflight

Use [mandatory preflight](02-execution-rules.md#mandatory-preflight).
Baseline 28a00c8 / 0.3.15 was confirmed; main had no open PR. Record discovered
plan details in [decisions](05-decisions.md), including provenance and wire kinds.

## Acceptance

Run the document-only acceptance in [execution rules](02-execution-rules.md).
Check every local link, seven group overviews, all per-PR sections/Version
decisions, planned API labels, conditional native-unlock prerequisites and
absence of original evidence/publication leakage. Parse Python snippets for
syntax, not imports of unimplemented APIs.

R0 must pass the sequential review/merge gate before R1 implementation starts.

## Local validation (2026-09-18)

Strict website build passed with no issues; website tooling tests passed (97).
All 31 plan documents, 169 local links/anchors and 11 Python snippets passed
structural/syntax checks. No snippets importing planned APIs were executed.
The diff check passed. No source code, package version or corpus was changed.
Remote CI and review are still required before this stage can advance.

## Version

Version: none, only internal plans and instruction/index pointers change.
