---
description: "Use when implementing user-described features, fixing bugs, refactoring, or generating new code. Enforces minimal abstraction, minimal scope expansion, dataclass-based config conventions, type hints, and core-logic test coverage with colocated `<source>_test.py` files."
applyTo: "**"
---

# Implementation and Core-Logic Tests

When implementing what the user described, follow these principles together. They constrain both the production code and the accompanying tests.

**Key rules at a glance** (use the numbered sections below for the full rules):
- Use the most direct structure; avoid extra abstraction layers.
- Implement only what the description asks for; mention out-of-scope improvements instead of adding them.
- Configure behavior through frozen, keyword-only `@dataclass` objects (mirror `ExecutionConfig` in `src/sciloom/core/interpreter/runtime.py`); validate in `__post_init__`.
- Type-hint public APIs; use enums for closed choice sets.
- Prefer TDD when feasible: write test logic first, then implement. Colocate tests in `<source>_test.py`; cover the primary path and the most likely failure patterns. Run them with `uv run pytest <path>`.
- If the description is incomplete or ambiguous, clarify with the user before proceeding. If it explicitly conflicts with the abstraction or config-shape guidance, follow the description and note the deviation; scope restrictions still apply unless the user explicitly requests otherwise.

## 1. Minimal Abstraction

Use the most direct code structure that satisfies the described requirement. If the user's description conflicts with these principles, prioritize the user's description and document the deviation.

- Do not introduce abstract base classes, factories, registries, generic protocols, plugin layers, or extra indirection unless the described requirement actually needs them.
- Do not split a single concrete implementation into multiple layers "for future flexibility".
- Inline a value or short helper when extracting it would only be used once and would not improve readability.
- Prefer concrete types and direct function/method calls over abstract types and dispatch when there is one real implementation today.
- Do not split a single-use operation into a public/private wrapper pair or a chain of one-off helper functions just to make individual functions shorter or easier to unit test. If the helper has no independent semantic role, no second caller, and no meaningful name beyond restating the caller, keep the logic in the caller.
- Prefer writing one cohesive function for one cohesive behavior. Extract a helper only when it names a distinct concept, removes meaningful duplication, isolates a genuinely complex sub-step, or is reused by multiple call sites.

If you find yourself adding a layer "in case we need to swap it later", stop and use the concrete form instead.
If you find yourself creating a function that only forwards to another function with nearly the same name, inline it unless there is a concrete lifecycle, validation, or API-boundary reason for the wrapper.

### Configuration Objects

This codebase configures behavior through immutable `@dataclass` objects, not ad-hoc dicts or long positional argument lists. `ExecutionConfig` (`src/sciloom/core/interpreter/runtime.py`), `AutoSuiteTarget` and the IR records follow the same conventions.

- Declare the config as `@dataclass(frozen=True, kw_only=True)`. Give optional knobs sensible defaults, plain values or `field(default_factory=...)` for mutable ones, so callers pass them by name.
- Validate in `__post_init__` and raise `ValueError` for an invalid value or combination, or `TypeError` for a wrong type, with a message that says what is accepted. Do not scatter the same validation across call sites. A frozen dataclass normalizes a field with `object.__setattr__`, as `AutoSuiteTarget` does for its version.
- Do not accept a plain mapping in place of a config object. Serialized data enters only through its existing validating boundary, such as `from_dict`/`from_json` in `sciloom.core.ir`; do not add a second, handwritten parser.
- For a closed set of choices, define a `StrEnum` (like `AutoSuiteVersion`) and accept the enum or its string value, normalizing in `__post_init__`.
- Keep required inputs, the concrete things a class needs to do its job such as the `Program` an `Interpreter` runs or the device profiles a target binds, as explicit parameters distinct from optional knobs. Do not funnel everything through `**kwargs`.

### Module Organization

Place code near the behavior that gives it meaning.

- Keep a primary class with its methods and tightly coupled helpers in one cohesive module (e.g. a target and its validation, or the interpreter and its `ExecutionConfig`).
- A config dataclass or enum lives beside the code that consumes it. Shared semantic vocabulary lives in `sciloom.core.ir`, and ownership between packages follows `AGENTS.md` §10. Do not create a catch-all module for unrelated types.
- Keep small private helper functions next to their single caller unless they are reused across modules.
- Tests live beside their source as `<source>_test.py` (see Section 3), not in a separate `tests/` tree.

## 2. Minimal Scope Expansion

Implement only what the user's description asks for.

- Do not add configuration options, flags, fields, methods, or task types that the description does not mention.
- Do not refactor unrelated code, rename unrelated symbols, or "clean up" nearby files while implementing the requested change.
- Do not add logging, metrics, retries, caching, or validation unless explicitly mentioned in the description or clearly required by the surrounding code. (The packages use no logging library: report problems through `Diagnostic`/`DiagnosticError` or ordinary exceptions rather than introducing a logging mechanism. Typed program logging is a language feature, not host logging.)
- If a related improvement seems valuable but is out of scope, mention it briefly to the user instead of silently adding it.

When in doubt, prefer the smaller change. The user can always ask for more.

## 3. Tests Cover Core Logic and Failure Patterns

Every implementation change must ship with at least one test file that exercises the core logic, with priority on the patterns most likely to fail.

When feasible, prefer a test-driven approach: write the test logic first to define the expected behavior, then write the implementation code to make those tests pass. This should be the default for new functions, config classes, and data/model flows; it is optional when changing existing code where the behavior or test boundary is not yet clear.

- Always generate or update a test file for the code you wrote or modified.
- Cover the primary success path of the described behavior.
- Cover the inputs and conditions most likely to break it: empty, missing or malformed input; boundary values; runtime source outside the supported subset; type mismatches; missing, unknown or incompatible device bindings; hand-built or edited IR and JSON; errors raised by dependencies; and any explicit precondition the code enforces (for example "max_steps must be a positive integer" or "device_id must be the positive decimal ID of an individual shaker"). Assert the diagnostic `code` a rejection carries, not only the exception type.
- Do not aim for exhaustive coverage of trivial properties, generated code, or thin pass-through wrappers. Aim for the logic that, if broken, would silently produce wrong behavior.
- Run the new tests with `uv run pytest <path>` and confirm they pass before reporting the task done.

### Test File Naming and Location

Colocate tests next to the source file and name them after that source file.

- For a source file `bar.py`, create or update `bar_test.py` in the same directory (e.g. `compiler.py` → `compiler_test.py`, `device_slots.py` → `device_slots_test.py`). An example keeps its test beside it too (`examples/stir_rack.py` → `examples/stir_rack_test.py`).
- Do not create a separate `tests/` tree, a generic `helpers_test.py`, or a catch-all file when a focused `<source>_test.py` companion already fits.
- If a single source file's tests grow large enough to warrant splitting, split by feature into additional files that still start with the source file's basename (for example `codegen_arrays_test.py` and `codegen_agitation_test.py` beside `codegen.py`).
- Use pytest conventions: test functions named `test_*`, fixtures over ad-hoc setup, and `pytest.mark.parametrize` for input variations.
- Production mypy traversal excludes `*_test.py`; when adding a test module under `src/` or `packages/`, also add it to the explicit test-module override list in `pyproject.toml`.

## 4. Verification Proportionate to the Change

Run the checks that exercise the changed behavior, proportionate to the change
type and its risk. Do not claim a check passed unless it was run in this change
and succeeded.

- A change to shipped code, configuration, examples or tests runs the full set
  in `AGENTS.md` §8, plus the focused tests for the touched modules.
- A change to `website/` runs the documentation build and tests listed in
  `AGENTS.md` §9.
- A change limited to `AGENTS.md`, `.github/instructions/`, `docs/` or other
  Markdown outside the website runs `git diff --check`; it does not owe the
  Python or website checks unless the changed files can affect them.
- Do not fix an unrelated pre-existing formatting, test or build failure in the
  current change; report it and let `branch-and-pr-workflow.instructions.md`
  decide whether it blocks.
- The final report separates: checks that passed for this change; failures this
  change caused; pre-existing, unrelated failures with their evidence; and
  checks that were not run, with the reason.

## Quick Self-Check Before Finishing

Before reporting an implementation as complete, confirm:

1. No abstraction was added that is not justified by the described requirement.
2. No feature, option, or refactor was added beyond the description.
3. Behavioral configuration goes through a frozen, keyword-only `@dataclass` with defaults and `__post_init__` validation, and required inputs stay explicit parameters separate from optional knobs.
4. No plain mapping stands in for a config object, serialized data enters only through its existing validating boundary, and closed choice sets use a `StrEnum`.
5. Public APIs are type-hinted, carry English Google-style docstrings, and follow the package ownership in `AGENTS.md` §10.
6. A `<source>_test.py` file exists next to the changed source and exercises the core path plus the most likely failure patterns.
7. The new and existing tests for the touched modules pass (`uv run pytest <path>`).
8. The verification report distinguishes passed, caused, pre-existing and not-run checks as Section 4 requires.
