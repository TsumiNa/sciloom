# Reference execution and the SciLoom semantic contract

SciLoom IR is a structured scientific-program model. It can be validated,
exchanged as JSON and executed without importing either a source frontend or
a target backend. The reference interpreter specifies the currently supported
semantics; it is not AutoSuite simulation and does not control hardware.

## Program and JSON v2

The root is `Program`, selecting an entry FunctionIR and containing specialized
function instances. Semantic IDs identify occurrences and ownership, never target
objects. JSON uses kind `Program` and explicit format_version `2`. Version 1 and
the old Package import are rejected rather than silently migrated.

`core/ir/schema.py` defines structural conversion independently of the JSON codec.
Both typed validation and the codec use it; semantic validation does not import
the codec. Common diagnostics and SourceSpan live outside the IR dependency graph.

## Developer example

Run `uv run python -m examples.developer.agitation_ir` from the repository root.
It reuses the Function in `examples/agitation.py`, persists its IR to
`examples/developer/agitation_ir.json`, reloads it and verifies start/stop behavior
in a reference session. The experiment-author example compiles directly to ASFP
and does not expose these development steps.

JSON serialization is optional: `Interpreter(function.to_ir())` works directly.
The example deliberately exercises persistence as a separate architectural check.

## Execution API

```python
from sciloom.core.interpreter import ExecutionConfig, Interpreter

session = Interpreter(program.to_ir(), config=ExecutionConfig(max_steps=10_000))
first = session.run(inputs={"amount": 3})
second = session.run(inputs={"amount": 2})
first.outputs
second.state
second.steps
```

Inputs use entry parameter names; state snapshots use semantic function and
variable IDs. Results contain detached, read-only output and state mappings.
The IR and source instance remain unchanged. A session is sequential, not intended
for concurrent run calls.

Internal variables initialize once when the session is created, with state owned
by their function ID. Repeated calls share that state; distinct specialized
instances do not. Input/output frames are fresh for every invocation, including
recursive calls. Inputs are copied in, never implicitly bound to caller storage.
Arguments are evaluated in IR binding order before entry; outputs are copied to
destinations in output-binding order after successful return. Aliased destinations
therefore receive the last bound value.

Uninitialized reads and outputs missing at normal return are execution errors.
Earlier state writes remain after a failing run; execution does not promise
transactional rollback. A new Interpreter starts a fresh session.

## Values, evaluation and failures

- Integer has mathematical-integer reference semantics. Real uses finite binary64
  values. Boolean is distinct from Integer. Integer-to-Real conversion is explicit
  in the evaluator at typed storage/parameter boundaries; narrowing is rejected.
- Division produces Real. Division by zero, nonfinite results and values too large
  to convert to Real raise ExecutionError with diagnostics.
- Expressions evaluate left to right; boolean AND/OR short-circuit. If and While
  require Boolean conditions. No host-Python truthiness or arbitrary functions
  participate in evaluating authored programs.
- max_steps defaults to 10,000; expressions, statements and function entries each
  consume a step. Empty loops are bounded because conditions consume steps.
- max_call_depth defaults to 64 and accepts 1–100, keeping the recursive reference
  evaluator within a conservative host-stack budget. Host nesting exhaustion is
  also converted to an execution diagnostic.

These are SciLoom semantics, not claims about AutoSuite numerical limits,
overflow behavior or error handling. AutoSuite rejects recursive programs.
Its AND/OR evaluation behavior is not verified by the supplied exports, so its
target currently rejects these operators with unsupported_short_circuit; use
explicit If statements. IR authoring and reference execution still support them.
A future backend legalization may translate short-circuit expressions into
explicit control flow. No backend may silently substitute eager evaluation.

## Verification boundary

Direct-IR, Python and JSON versions of the same stateful program have matching
outputs across calls. Tests also cover shared/distinct instances, recursive frames,
loops, dead-expression short-circuiting, runtime faults, immutable snapshots and
budget exhaustion. A subprocess blocks imports of all frontends and backends
while executing JSON IR.

Existing AutoSuite golden comparisons validate serialized structure and reference
relationships. Executor acceptance, physical behavior and vendor numeric edge
cases require separate target evidence and integration tests.
