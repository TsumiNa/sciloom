# Reference execution

Interpreter executes typed IR without generated Python or equipment imports. It
defines SciLoom semantics, not vendor simulation or hardware behavior.

```python
from examples.scale_values import ScaleValues
from sciloom.core.interpreter import ExecutionConfig, Interpreter, ReferenceEnvironment

session = Interpreter(ScaleValues().to_ir(), config=ExecutionConfig(max_steps=10_000))
result = session.run(inputs={"values": [1.0, 2.0, 3.0], "factor": 2.5})
assert result.outputs["result"] == (2.5, 5.0, 7.5)
```

JSON persistence is optional. The [agitation IR example](../../examples/agitation-ir.md)
deliberately exercises it to verify the boundary. DeviceIf requires specialization
before interpreter construction; after compilation use result.specialized_ir.
Native commands without reference semantics fail explicitly.

## Explicit environment

Pass `environment=ReferenceEnvironment()` to make external-context ownership
explicit. Omitting it creates a fresh environment for that Interpreter. Pure
calculation and existing device programs keep their previous calling convention.
The environment does not read host files, sample a real clock or confirm messages
automatically. Concrete services arrive with the operations that need them.

Using the imports above:

```python
environment = ReferenceEnvironment()
session = Interpreter(ScaleValues().to_ir(), environment=environment)
result = session.run(inputs={"values": [1.0, 2.0, 3.0], "factor": 2.5})
assert result.outputs["result"] == (2.5, 5.0, 7.5)
assert environment.events == ()  # This calculation has no external events.
```

`environment.events` returns an immutable history snapshot across all runs using
that environment. `result.events` remains limited to one successful run.
`ExecutionEvent` is the union of DeviceEvent, LogEvent, AcknowledgementEvent,
WallTimeEvent, TimerEvent, WaitEvent and CsvReadEvent. Narrow with
`isinstance(event, LogEvent)` before accessing log-specific fields; device events
carry state snapshots. A failed run leaves earlier completed events in
environment history and does not roll back their state changes.

Reuse the same environment to share history explicitly. This does not share
Function variables or device configurations between Interpreters. Child Function
calls use their entry session's environment. Sessions and environments are
sequential and are not intended for concurrent execution.

The [environment example](../../examples/reference-environment.md) runs two
sessions and inspects their combined history and independent device snapshots.

## Typed log events

`LogValue` evaluates its value, category and stream once in that order. It appends
a LogEvent only after all three succeed, so a failed argument does not leave a
partial log record. Logs from child calls, loops and device actions share the
same ordered event tuple. The event stores the operation ID/source, ScalarType,
native scalar or public quantity value, and both captured labels. It does not
read a device or require a file service.

The [direct logging IR example](../../examples/logging-ir.md) constructs a volume
log, restores JSON v4 and inspects the typed event. Prior records retain their
values when fields change or the session runs again.

## Explicit confirmation

Give a program containing Notify a finite set of OK responses:

```python
from examples.confirm_samples import ConfirmSamples
from sciloom.core.interpreter import Interpreter, QueuedAcknowledgements, ReferenceEnvironment

responses = QueuedAcknowledgements([True])
environment = ReferenceEnvironment(acknowledgements=responses)
session = Interpreter(ConfirmSamples().to_ir(), environment=environment)
result = session.run(inputs={"sample": "A"})
assert responses.remaining == 0
assert len(result.events) == 2  # Acknowledgement, then log.
```

Notify evaluates its message once, then consumes one response. Only a successful
acknowledgement appends an AcknowledgementEvent, with the captured text and source.
An absent service raises `missing_environment_service`; an exhausted queue raises
`acknowledgement_required`. No prompt opens, no default is supplied, and later
statements do not run. A bad message expression fails before consuming a response.

Only literal `True` responses are accepted. The constructor copies the iterable.
Sharing a service or environment explicitly shares its remaining responses;
omitting the service never confirms a message. A later failure preserves already
consumed responses and completed events. Calling `run()` again starts at the
entry, rather than resuming the failed statement.

The [direct IR example](../../examples/confirmation-ir.md) shows JSON restoration
and a typed acknowledgement event. This reference behavior does not establish
that a generated AutoSuite dialog blocks correctly on the target host.

## Wall-clock input

Provide a WallClock service for ReadWallTime. VirtualWallClock returns the aware
instant supplied by the caller until `set()` changes it:

```python
from datetime import datetime, timedelta, timezone
from examples.timestamp_path import TimestampPath
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualWallClock

clock = VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone(timedelta(hours=9))))
environment = ReferenceEnvironment(wall_clock=clock)
result = Interpreter(TimestampPath().to_ir(), environment=environment).run(inputs={"directory": "results"})
assert result.outputs["path"] == "results/2026-09-16_140506.csv"
assert len(result.events) == 1
```

A custom service implements `now() -> datetime`. Each ReadWallTime calls it
once, validates an aware datetime, formats it without host locale/timezone
conversion, then writes the field and records a WallTimeEvent. The event holds
the source, format and text, not the provider or a mutable timezone object.

No service means `missing_environment_service`. A provider exception or invalid
datetime becomes `wall_clock_error`; the destination and event history are not
partially updated. Earlier completed effects remain. Separate environments do
not share clocks unless explicitly given the same service. This wall clock is
independent of elapsed-time waits; it does not advance automatically.

The [direct IR example](../../examples/wall-time-ir.md) also checks JSON v4 restoration.

## Elapsed-time input

Supply `ReferenceEnvironment(clock=VirtualClock())` for Wait, StartTimer and
WaitUntil. VirtualClock stores finite nonnegative seconds and advances without
sleeping. It is independent of VirtualWallClock: a wait does not change supplied
calendar time. Omitted clocks cause `missing_environment_service`, even for a
zero wait. `VirtualClock(start=...)` accepts an explicit nonnegative origin.

StartTimer captures the current monotonic value. WaitUntil evaluates its Duration
once, verifies a start in this entry run, then waits only for time still missing
from the threshold. Negative requests fail with `wait_duration`; invalid clock
advances or overflow fail with `clock_error` before changing the clock. Earlier
completed events and state changes remain. Timer validity resets at each entry
run; child calls share the entry's time axis and Function-owned timer identities.

Successful starts append TimerEvent with the new origin. WaitEvent records the
requested Duration, monotonic start/end of the wait, and a timer ID for elapsed
waits (None for ordinary waits). Already elapsed waits have equal start/end times.
These events are immutable and interleaved with device and log events. The
existing `result.resources` mapping continues to contain device states only.

The [timer IR example](../../examples/timing-ir.md) advances five virtual seconds.
This defines ordering and elapsed-time semantics; it is not a latency or scheduling
simulation of AutoSuite or physical equipment.

## Explicit files and CSV outcomes

Provide `ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data_bytes}))`
for isolated reference reads. MemoryFiles copies its initial mapping; immutable
byte snapshots stay unchanged after later appends. Each newly constructed service
has independent state. Sharing a service explicitly shares its file contents.

Use `LocalFiles(root=...)` only when host file access is intended. The root must
already be a directory. Paths are relative to it; absolute paths, traversal and
resolved symlinks outside it are rejected. This containment check is not a sandbox
against concurrent filesystem changes. FileService exposes `read_bytes(path)` and
`append_bytes(path, data)`; append creates a missing file but never parent directories.
Runtime CSV append is not available yet.

ReadCsv captures path, optional row, then each column's index/default once before
reading. It parses and converts all results, normalizes them for destinations,
then commits them together. Lists use the usual immutable internal representation.
A failed ordinary read leaves every destination unchanged. The
[CSV reference](../../user-guide/reference/csv.md) defines encoding, conversions,
try-form fallbacks and named statuses; it does not promise a filesystem transaction.

CsvReadEvent records a completed read attempt, including IO/parse/EOF failures,
with captured path, selectors and status. It is appended before result assignment
or a fatal diagnostic. Invalid arguments or a missing file service produce no
read event. Even if destination normalization subsequently fails, the completed
file-read event remains. Previously completed actions are not rolled back.

The [CSV IR example](../../examples/csv-read-ir.md) demonstrates JSON restoration
without reading a host file. Native AutoSuite task probes remain separate from
portable compilation and cannot establish parser equivalence by static inspection.

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

| Budget | Default | Range |
|---|---|---|
| `max_steps`: expressions, statements and function entries | 10,000 | positive |
| `max_call_depth` | 64 | 1 to 100 |
| host nesting | the interpreter's own recursion | exhaustion becomes a diagnostic |

These limits bound reference work and say nothing about real equipment timing or
numeric limits.
