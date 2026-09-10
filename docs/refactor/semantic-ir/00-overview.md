# Semantic IR implementation sequence

Accepted scope: build a typed semantic model, then the restricted Python frontend,
then prove Python → ASFP against retained AutoSuite fixtures. The public compiler
entry point is `instance.compile()`. This is compilation even though the output
is another source representation.

## Decisions

- Immutable dataclasses and enums describe semantics; JSON is a versioned
  representation of those same objects. It has no XML IDs or GUI coordinates.
- A Function class declares its static runtime schema. `Input[T]` and `Output[T]`
  are explicit roles; a plain SciLoom type (`index: Integer = 0`) declares internal
  runtime state. Ordinary Python types and instance attributes are host-time data.
  The earlier `Local[T]` spelling is superseded.
- Only ordinary `.py` source is supported initially. Registered runtime methods
  are parsed, never executed to infer control flow.
- Internal variables retain target initialization semantics; explicit assignment
  resets a variable on every invocation. The backend introduces Macro scope as needed.
- Future Application fields declare globals. Functions declare `GlobalRef[T]`
  dependencies and bind them with `bind_globals(name=app.ref("name"))`. References
  identify shared state, not copied values. Application compilation checks ownership
  and types; standalone ASFP dependencies must be reported. This API is deferred.
- Prefer explicit ownership and symbol references over name-based global lookup.
  Do not introduce a second `transpile()` entry point or public XML mechanics.

## Ordered PRs

1. [Typed IR with validated JSON](01-semantic-ir-json.md).
2. [Restricted Python lowering](02-python-frontend.md).
3. [ASFP compilation](03-asfp-backend.md).

The plan is included with PR1. Each PR must pass its own checks, complete review,
address feedback and be squash-merged before implementation of the next begins.

## Non-goals

Application/global binding implementation, event handlers, hardware tasks, arrays,
physical units, Notebook/interactive/exec source, GUI pages, AI services, ASFP
import, and canonical Python regeneration are outside this first sequence.

## Validation

Colocated pytest tests cover semantic success and failure cases. Every stage runs
the existing corpus smoke and recipe checks and syntax-checks design examples.
Original AutoSuite evidence is never rewritten. XML comparison checks structure
and reference relationships, not arbitrary timestamp/UUID equality. Executor
acceptance remains a separate integration gate on an AutoSuite host.
