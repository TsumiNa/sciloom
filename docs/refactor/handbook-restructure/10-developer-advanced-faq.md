# Developer Guide advanced and FAQ

## Goal

Complete the Developer Guide with Advanced, FAQ and Troubleshooting pages and
the contributor half of the glossary.

## Scope

- `advanced/json-interchange.md`: executed program on
  `examples.developer.portable_agitation` (round trip equality; selected device
  types differ from authored); what survives a round trip; why authored JSON
  names the family; repository-relative source spans.
- `advanced/specialization.md`: the executed program moved from
  `reference/pipeline.md`; the internals (validate, bindings, selection, pruning,
  retyping, re-validate; missing bindings are errors even for a false query).
- `advanced/native-commands.md`: `DeviceCommand` semantics, why the interpreter
  refuses it, how AutoSuite lowers device intent (today's "AutoSuite boundary").
- `advanced/extending-the-analysis.md`: the recognizer and lowering conventions
  from today's architecture page, in the site's own words.
- `advanced/typing-without-inheritance.md`: from the old target tutorial's
  typing section and the typing page's second and third paragraphs.
- `faq.md`: do I change SciLoom to add my instrument; family or profile; why the
  Function names the family; why capability lists are not inherited; why my
  family's required configuration is not enforced; why the interpreter cannot run
  my command; reject or adapt; why `resolve_devices` sees a different program;
  may a target import `sciloom.flow`; does compiling prove hardware behaviour;
  which minimal target to copy.
- `troubleshooting.md`: `TypeError` at host time, `ValueError` from bindings,
  `IRValidationError`, `CompilationError`, `ExecutionError`; one row per code
  with message fragment, what it proves, fix.
- `website/docs/introduction/glossary.md`: the "Contributor terms" section (family, profile,
  slot, contract, binding, target, artifact, authored versus selected program,
  specialization, definite configuration, semantic id, diagnostic, native
  command, reference execution).
- Register the two executed Advanced programs in the first-fence list; replace
  the tutorial's transitional notes with links; nav.

## Non-goals

No change to the tutorial's code. No `api/` change.

## Acceptance

- Every code in `troubleshooting.md` exists in `src/` or `packages/`.
- No fact from the [ownership table](00-overview.md#ownership) is stated on two
  pages, except the two short/long and teaching/table pairs the table names
  (checked by grepping each owner's key phrase).
- `uv run --group docs pytest website/tools`; `uv run --group docs python website/tools/site.py build --strict`.
- `git diff --check`.

## Version

`Version: none, documentation and test tooling`.
