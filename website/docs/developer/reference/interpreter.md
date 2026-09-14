# Reference execution

Interpreter executes typed IR without generated Python or equipment imports. It
defines SciLoom semantics, not vendor simulation or hardware behavior.

```python
from examples.scale_values import ScaleValues
from sciloom.core.interpreter import ExecutionConfig, Interpreter

session = Interpreter(ScaleValues().to_ir(), config=ExecutionConfig(max_steps=10_000))
result = session.run(inputs={"values": [1.0, 2.0, 3.0], "factor": 2.5})
assert result.outputs["result"] == (2.5, 5.0, 7.5)
```

JSON persistence is optional. The [agitation IR example](../../examples/agitation-ir.md)
deliberately exercises it to verify the boundary. DeviceIf requires specialization
before interpreter construction; after compilation use result.specialized_ir.
Native commands without reference semantics fail explicitly.

## Session and snapshots

Internal variables initialize once per session and function identity. Repeated
calls retain state; a new Interpreter starts a fresh session. Input/output call
frames are fresh. Inputs are copied in and outputs copied back after normal return.
Results expose detached read-only output/state/resource mappings; lists appear as
tuples, so later calls cannot mutate earlier snapshots.

Inputs are evaluated in IR binding order before entry. Outputs copy back in
output-binding order after successful return; aliased destinations receive the
last bound value. Output and state snapshots use entry names and semantic IDs,
respectively. Host list inputs accept lists or tuples, and quantity values are
restored to physical types in public outputs.

Device snapshots separate saved configuration, applied configuration and enabled
state. Configure captures immediately, start applies complete saved values, and
stop retains configuration. Events preserve snapshots at each operation.

Uninitialized reads and missing outputs are execution errors. Earlier state writes
remain after a failed run: execution is not transactional. A session is sequential
and is not intended for concurrent run calls.

## Numerical and execution limits

Integers use mathematical-integer semantics; floats are finite binary64. Booleans
are distinct. Division by zero, nonfinite results and invalid float conversions
raise ExecutionError. Expressions evaluate left to right; and/or short-circuit.
List bounds checks reject negative, Boolean and out-of-range indices without growth.

An ordinary indexed assignment evaluates its RHS before the target/index access.
An augmented indexed assignment reads and checks the selected element/index once
before evaluating the RHS. A failure does not undo earlier state writes.

ExecutionConfig defaults to 10,000 steps and call depth 64. Expressions, statements
and function entries consume steps. Configured call depth must be within 1–100;
host nesting exhaustion becomes a diagnostic. These limits bound reference work
and say nothing about real equipment timing or numeric limits.
