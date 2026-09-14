# User Guide FAQ, troubleshooting and glossary

## Goal

Give authors the three pages they open when something is unclear or fails.

## Scope

- `user-guide/faq.md`: questions with a two-sentence answer and one link. Why no
  `for`; why no `return`; no local variables; `Var` does not reset; no `Input`
  defaults; zero speed is not a stop; no reading a device property; `and`/`or`
  rejected by AutoSuite; an unused slot still needs a binding; whole-list outputs;
  running without hardware; supported AutoSuite versions; notebooks and REPLs;
  sharing one shaker; one program for two instruments; docstrings; where codes
  are explained.
- `user-guide/troubleshooting.md`: opens with a "Reading a diagnostic" program
  (executed first fence, output asserted), then tables grouped by when the error
  fires (class creation, host access to a runtime field, source analysis, type
  checking, target compilation), each row `Code | Message | Cause | Fix`, the
  fix carrying the link to the explaining page, followed by the host-time
  `TypeError`/`ValueError` messages. Messages are verbatim from source.
  Codes that arise only from hand-built IR or reference execution are left to the
  Developer Guide page.
- `website/docs/introduction/glossary.md` (the publication check allows only the
  existing directories at the site root, so the glossary lives under
  Introduction, where its nav entry is) with the "Authoring terms" section (Function,
  runtime method, host time, Input/Output/Var, host configuration, child Function,
  logical device and slot, profile, binding, target, artifact, compile-time query,
  specialization, definite configuration, diagnostic, rotational speed, whole-list
  assignment, zone and device id, AutoSuite Executor, reference execution); the
  "Contributor terms" heading is added with a one-line placeholder that PR 10
  fills. Nav entry under Introduction; `user-guide/index.md` links it.
- `website/mkdocs.yml` and `website/tools/handbook_test.py` (troubleshooting
  first fence).

## Non-goals

No Developer Guide content. No change to the tutorial or Advanced pages beyond
closing links.

## Acceptance

- Every message in the troubleshooting tables is found by
  `grep -rn "<message>" src packages`.
- `uv run --group docs python website/tools/site.py build --strict` (every
  `See` link and anchor resolves).
- `uv run --group docs pytest website/tools`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
