# Runtime capability interface contract

## Status and ownership

This is the authority for the [implementation sequence](00-overview.md). All new
signatures and snippets below are **target interfaces** until their stated stage
lands. They have not been executed. Existing Program/JSON v4, Function.compile,
device property/command contracts and the Target protocol are current.
Stages 1–4 implement section 1's explicit wire identities, section 3's text,
section 4's quantity interfaces and section 5's numeric operations. Later sections remain target
contracts until their owning stage lands.
Stage 5 adds section 2's environment injection and event history. Its concrete
service setup examples remain target interfaces until the listed consuming stage.
Stage 6 implements section 6's log call, LogValue and LogEvent. Stage 7 implements
section 7's notify call, Notify and explicit acknowledgement service. Stage 8
supplies failure probes while retaining the unverified Executor gate. Stage 9
implements section 8's now_text call, ReadWallTime and explicit wall clock.
Stage 10 implements section 9's Function-owned timers, waits and virtual clock.
Their runnable examples and tests verify reference semantics and static mappings;
none establishes Executor acceptance. Stages 11–17 remain target contracts.

Experiment authors import from `sciloom`; targets from `sciloom_autosuite` or an
independent package. `flow` declares author vocabulary; `dsl` alone analyzes
Python; `core` owns typed semantics and imports neither. Units remain independent.
No runtime method body executes while compiling. Ordinary Python constructors
compose/specialize the instance; class declarations define its runtime fields.

## 1. Durable IR and JSON (stage 1)

One dataclass/type definition drives structural checking and both codec
directions. Semantic validation separately checks values, references and flow.
Every serializable record declares a unique, stable class-level `__ir_kind__`.
Existing names, fields, enum values and defaults retain their wire meaning.

Illustrative change to the existing class (not a second user-defined node):

```python
from dataclasses import dataclass
from typing import ClassVar

from sciloom.core.ir.model import Expression, Node


@dataclass(frozen=True, kw_only=True)
class ListLength(Node):
    __ir_kind__: ClassVar[str] = "ListLength"

    value: Expression
```

An internal class rename leaves `__ir_kind__` unchanged. The codec must reject
missing and duplicate kinds, including subclasses that merely inherit a parent's
kind. Derive reachable record types from the typed schema, not a second hand-kept
registry. Keep wire field names stable rather than add aliases preemptively.
Unknown fields/kinds/types/enums fail explicitly; JSON never imports Python IDs.

Retain these current functions and behavior:

```python
from sciloom.core.ir import Program, from_dict, from_json, to_dict, to_json, validate


def restore(program: Program) -> Program:
    restored = from_json(to_json(program))
    assert restored == program
    assert to_json(from_dict(to_dict(program))) == to_json(program)
    assert validate(restored) == ()
    return restored
```

`format_version` remains 4. New implementations read old valid documents; old
implementations may reject new vocabulary. Adding a kind or scalar enum does not
make old documents need migration. Existing canonical JSON remains byte-identical
through the foundation refactor, preserving existing AutoSuite identity hashes.
No `required_features` list, eager future nodes, alternate reader or migration
command is introduced. If an existing meaning must change, stop and revise the
design explicitly rather than silently repurpose its kind or bump the format.

Reuse ConfigureProperty and DeviceCommand for declared properties and no-return
device commands. Their stable semantic IDs already permit contributor additions.
Add typed high-level nodes for new results, value types, control flow and scopes.
Use enums within a family only when its parameter structure and execution rules
match. Keep Call, If, While, existing list and agitation nodes intact.

All consumers explicitly handle supported nodes and reject unsupported ones.
Remove remainder-as-Call/Binary dispatch. Type exhaustiveness and node-set tests
cover structural validation, expression typing, resource/configuration analysis,
specialization, reference execution and target generation. Generic traversal does
not replace branch intersection or zero-iteration analysis. No opaque skip path.

## 2. Evaluation, state and reference environment

Values are immutable in IR and reference storage. Assignment and parameter/result
passing retain list value-copy behavior. Initial Var values persist between calls
in a session and are isolated across instances/sessions. Zone values are immutable
ordered unique well references; they are not text or device profiles.

Expressions evaluate in their specified order and Boolean operators short-circuit.
Effectful reads, writes, clock access, messages, waits, logs and device actions
are ordered statements. They cannot be duplicated or moved as pure expressions.
First-version result-bearing external calls occupy an entire assignment RHS;
capture their result in declared fields before further computation. Parameters
are captured once at operation entry. New external reads use distinct multi-result
destination fields and commit results together after accepting them. This does
not retroactively change existing Call output-binding or return-copy semantics.
A failure does not roll back earlier state changes, device actions or file writes.

Stage 5 extends, without breaking existing calls:

```python
from sciloom.core.interpreter import ExecutionConfig, Interpreter, ReferenceEnvironment

environment = ReferenceEnvironment()
session = Interpreter(program, config=ExecutionConfig(), environment=environment)
result = session.run(inputs={})
```

The environment is an explicit runtime dependency, never serialized in Program.
Its services arrive with their features: memory files / opt-in local-file adapter,
virtual monotonic and wall clocks, fixed location directory, mutable well-property
store, and queued acknowledgement responses. No default host-file or real-clock
read, automatic acknowledgement, or process-global service. A missing required
service is an execution error. Fresh environments are isolated; explicitly reused
ones represent shared external state and must be documented as such.

Retain ExecutionResult outputs/state/resources and existing DeviceEvent data for
old programs. Extend the ordered event union for external events; retain immutable
snapshots after later calls. Stage 16 adds physical-device snapshots rather than
pretending one logical resource can represent several physical running states.

### Environment ownership and service contracts

Stage 5 implements only `ReferenceEnvironment()`, its event history, the
Interpreter keyword above, and the internal missing-service diagnostic boundary.
There are no file/clock/location/acknowledgement placeholder implementations in
that stage. The following service signatures are **target contracts**; constructor
keywords become available in the listed stage.

| Stage | Environment keyword | Service |
| --- | --- | --- |
| 7 | `acknowledgements` | `QueuedAcknowledgements` |
| 9 | `wall_clock` | `WallClock`, normally `VirtualWallClock` |
| 10 | `clock` | `VirtualClock` |
| 11 | `files` | `FileService`, `MemoryFiles` or explicit `LocalFiles` |
| 13 | `locations` | `LocationDirectory` |
| 15 | `properties` | `WellProperties` |

Services are owned by the caller when injected; the interpreter never clones
them. Reuse one environment, or the same service object in two environments,
to share external state explicitly. Omitted environments are fresh per
Interpreter; all service fields default to None as they are added. Child
Function calls use the entry session's environment. Device and Function state
remain session-owned even when an environment is shared.

`ReferenceEnvironment.events: tuple[ExecutionEvent, ...]` is a detached,
chronological history of completed events across every run using that environment.
`ExecutionResult.events` remains the per-run tuple. `ExecutionEvent` is a closed
union, initially DeviceEvent; each feature adds its own immutable event record.
No string-to-handler registration or arbitrary payload dictionary is introduced.
Earlier successful events remain in environment history after a later failure.
A failed operation does not invent a success event. These APIs are sequential,
not a thread-safe or transactional execution service.

Access to an absent required service raises `ExecutionError` with code
`missing_environment_service`, the service name, and the requesting IR node/source.
The internal `_require_service(service, name, node)` helper establishes this
boundary; no public generic service registry is added. Concrete adapters raise
ordinary I/O or lookup errors, which their IR operation handler translates to
its specified fatal diagnostic or explicit try-result. Missing service configuration
is never disguised as a CSV IO_ERROR or a user acknowledgement.

#### Files (stage 11, consumed by stages 11–12)

Signatures live in `sciloom.core.interpreter.files` and are re-exported from
`sciloom.core.interpreter` when implemented:

```python
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

class FileService(Protocol):
    def read_bytes(self, path: str) -> bytes: ...
    def append_bytes(self, path: str, data: bytes) -> None: ...

class MemoryFiles:
    def __init__(self, initial: Mapping[str, bytes] | None = None) -> None: ...
    def read_bytes(self, path: str) -> bytes: ...
    def append_bytes(self, path: str, data: bytes) -> None: ...
    def snapshot(self) -> Mapping[str, bytes]: ...

class LocalFiles:
    def __init__(self, root: str | Path) -> None: ...
    def read_bytes(self, path: str) -> bytes: ...
    def append_bytes(self, path: str, data: bytes) -> None: ...
```

MemoryFiles copies its initial mapping; keys are opaque path strings, and values
are immutable bytes. Reading a missing key raises FileNotFoundError. Appending
creates a missing file key and adds the bytes; snapshots are detached/read-only.
Empty or NUL-containing paths are invalid. CSV decoding, logical records, units
and default policies belong to the CSV operation, not the byte adapter.

LocalFiles is opt-in and never selected implicitly. Its root must be an existing
directory. Operation paths are relative to that root; absolute paths and escapes
through traversal or symlinks are rejected. It does not create parent directories.
OS file errors propagate; appends can have partial external effects on failure
and provide no rollback or concurrency guarantee. Paths on the actual AutoSuite
host remain deployment-specific, not remapped by the reference adapter.

Example runnable after stage 11:

```python
from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment

files = MemoryFiles({"recipe.csv": b"id,volume\nA,1.5\n"})
environment = ReferenceEnvironment(files=files)
session = Interpreter(recipe_program, environment=environment)
result = session.run(inputs={"path": "recipe.csv"})
# A matching two-column recipe program returns ("A",) and (1.5 * mL,).
# Reusing files shares bytes; creating MemoryFiles again starts independently.
```

#### Wall and monotonic clocks (stages 9 and 10)

Signatures live in `sciloom.core.interpreter.clocks`:

```python
from datetime import datetime
from typing import Protocol

class WallClock(Protocol):
    def now(self) -> datetime: ...

class VirtualWallClock:
    def __init__(self, instant: datetime) -> None: ...
    def now(self) -> datetime: ...
    def set(self, instant: datetime) -> None: ...

class VirtualClock:
    def __init__(self, *, start: float = 0.0) -> None: ...
    def monotonic(self) -> float: ...
    def wait(self, seconds: float) -> None: ...
```

Wall times must be timezone-aware; a naive datetime is rejected. VirtualWallClock
returns its supplied instant until explicitly set. Each now_text operation calls
now exactly once, then formats that captured value. VirtualClock owns finite,
nonnegative seconds; wait advances it without real sleeping, rejects negative,
Boolean or nonfinite durations, and validates the new value before changing state.
Timer origins belong to the Function session, not to the shared clock service.
Wall and monotonic clocks are independent; waiting does not implicitly change a
VirtualWallClock. A custom WallClock can explicitly derive its time from a shared
VirtualClock if a test needs that relationship.

Example runnable after stage 10:

```python
from datetime import datetime, timezone
from sciloom.core.interpreter import (
    Interpreter, ReferenceEnvironment, VirtualClock, VirtualWallClock,
)

clock = VirtualClock()
environment = ReferenceEnvironment(
    clock=clock,
    wall_clock=VirtualWallClock(datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)),
)
result = Interpreter(timed_program, environment=environment).run()
# For timer.start(); wait(2*s); timer.wait_until(5*s):
assert clock.monotonic() == 5.0
```

#### Acknowledgement (stage 7)

Signatures live in `sciloom.core.interpreter.acknowledgements`:

```python
from collections.abc import Iterable

class QueuedAcknowledgements:
    def __init__(self, responses: Iterable[bool] = ()) -> None: ...
    @property
    def remaining(self) -> int: ...
    def acknowledge(self, message: str) -> None: ...
```

The constructor copies the response sequence and accepts only True entries:
the current operation has OK confirmation, no cancellation/recovery result.
acknowledge consumes exactly one response; exhaustion raises LookupError,
translated by notify to `acknowledgement_required`. No service or empty queue
ever auto-confirms. Successful acknowledgement records a typed event with the
captured message before any following operation executes.

Example runnable after stage 7:

```python
from sciloom.core.interpreter import (
    Interpreter, QueuedAcknowledgements, ReferenceEnvironment,
)

responses = QueuedAcknowledgements([True])
session = Interpreter(
    one_notification_program,
    environment=ReferenceEnvironment(acknowledgements=responses),
)
session.run()
assert responses.remaining == 0
# A second run fails with acknowledgement_required before its next operation.
```

#### Fixed locations (stage 13) and stored properties (stage 15)

Signatures live in `sciloom.core.interpreter.locations` and
`sciloom.core.interpreter.properties`. Identifiers are data, never import paths.
Zone runtime values use ordered well identities; these directory interfaces do
not depend on the author's Python Zone class.

```python
from collections.abc import Mapping
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class WellLocation:
    well_id: str
    label: str
    controller_id: str | None = None
    device_type_id: str | None = None

class LocationDirectory:
    def __init__(
        self, *, wells: tuple[WellLocation, ...],
        zones: Mapping[str, tuple[str, ...]],
    ) -> None: ...
    def find(self, name: str) -> tuple[str, ...]: ...
    def describe(self, well_id: str) -> WellLocation: ...

class WellProperties:
    def __init__(
        self, initial: Mapping[tuple[str, str], str] | None = None,
    ) -> None: ...
    def get(self, well_id: str, name: str) -> str: ...
    def set(self, well_ids: tuple[str, ...], name: str, value: str) -> None: ...
    def snapshot(self) -> Mapping[tuple[str, str], str]: ...
```

LocationDirectory copies and freezes inputs. Well identities are unique; zone
members must exist, be ordered and not repeat. find returns an empty tuple for
an unknown name; describe raises KeyError for an unknown identity. Labels are
display text, not identities or positional indexes. Controller facts are optional
for storage-only wells; at/device selection requires complete trusted deployment
facts and compatible candidates. AutoSuiteLayout derives those facts from the
read-only APP and explicit target profiles in stages 13/16, not guessed names.

WellProperties copies the initial text mapping, keyed by (well identity, property
name). Missing values raise KeyError. set validates its complete input and then
assigns the same captured text to every selected identity. The IR handler checks
membership in the location directory before calling the store. Its snapshots
are detached/read-only; independent instances do not share property values.

Example runnable after stage 15:

```python
from sciloom.core.interpreter import (
    Interpreter, LocationDirectory, ReferenceEnvironment, WellLocation, WellProperties,
)

locations = LocationDirectory(
    wells=(WellLocation(well_id="rack/1", label="1"),),
    zones={"rack": ("rack/1",)},
)
properties = WellProperties({("rack/1", "sample_ID"): "A"})
environment = ReferenceEnvironment(locations=locations, properties=properties)
result = Interpreter(label_program, environment=environment).run()
# If label_program writes "B" to sample_ID on rack/1:
assert properties.snapshot()[("rack/1", "sample_ID")] == "B"
```

These are service setup examples, not complete experiment programs. Their named
Program inputs arrive with the consuming feature tests/examples; no unimplemented
snippet is claimed to have executed at stage 5.

## 3. Text (A01, stage 2)

Target author signatures:

```python
from sciloom import Input, Output, Var, text

name: Input[str]
labels: Output[list[str]]
cleaned: Var[str] = ""

# Inside @runtime:
self.cleaned = text.trim(self.name)
self.cleaned = self.cleaned + "_processed"
```

- `text.trim(value: str) -> str`: remove leading/trailing space, tab, CR and LF;
  do not claim the larger Unicode whitespace set of Python str.strip.
- `text.split_part(value: str, delimiter: str, index: int) -> str`: split by a
  nonempty delimiter, retain empty pieces; a missing piece returns empty text.
  Negative/Boolean indices are errors. Arguments may be runtime expressions.
- Builtin `len(value)` accepts text and returns int. Add text literals, defaults,
  scalar/list inputs, outputs, assignment, concatenation and equality/inequality.
- No implicit number-to-text conversion, text truthiness, arbitrary str methods,
  regex or slicing. XML escaping and expression-string quoting are separate.

Expected examples: trim `"  A\t"` gives `"A"`; split `"a,,b"` on `","` at 1
gives `""`, at 2 gives `"b"`, and at 7 gives `""`. Probe non-BMP Unicode length,
quotes, backslashes and embedded newlines before platform equivalence claims.

### Stage-2 implementation interfaces

The root `text` export is the declaration module `sciloom.flow.text`. Its typed
`trim(value: str) -> str` and `split_part(value: str, delimiter: str, index: int) -> str`
markers are valid in runtime source; calling them from host Python raises
TypeError. DSL resolution checks object identity and does not execute descriptors
or similarly named user functions. Both positional and named arguments follow
these signatures; variadic argument expansion remains unsupported.

IR adds `ScalarType.TEXT = "text"` and three expressions. Existing ListLength
retains its list-only meaning. Python len selects the expression using the
validated argument type. Text length counts Unicode code points, as Python len
does; there is no normalization or implicit encoding conversion.

```python
from sciloom.core.ir import Literal, ScalarType, TextLength, TextSplitPart, TextTrim

value = Literal(node_id="raw", type=ScalarType.TEXT, value=" a,,b ")
cleaned = TextTrim(node_id="clean", value=value)
part = TextSplitPart(
    node_id="part", value=cleaned,
    delimiter=Literal(node_id="delimiter", type=ScalarType.TEXT, value=","),
    index=Literal(node_id="index", type=ScalarType.INTEGER, value=2),
)
length = TextLength(node_id="length", value=part)
# Used as an assignment RHS in a valid Program: part is "b"; length is 1.
```

The constructors inherit Node's `node_id` and optional `source`; their stable
kinds are their displayed names. TextTrim/TextLength each take `value: Expression`;
TextSplitPart takes `value`, `delimiter`, and `index`, all Expressions, evaluated
left to right. They are pure expressions; invalid split arguments fail reference
execution with `text_delimiter` or `index_bounds`, while non-integer indices
fail semantic typing with `index_type`.

The AutoSuite profile uses text parameters/storage and the documented
TextLength, TrimText and SplitTextAndGet operations. Single-quoted literal
segments and documented Char codes represent apostrophes, backslashes and ASCII
control characters; XML escaping remains separate. NUL/invalid XML characters
receive a target diagnostic. These mappings are static/manual evidence, not an
Executor claim for Unicode length, whitespace or encoding.

AutoSuite length is limited to literal BMP text until its non-BMP counting rule
is verified. A runtime `str` can contain non-BMP characters, so unconstrained
runtime length receives `unsupported_text_length` rather than silently assuming
the platform counts Python code points. This is a target limit, not an IR limit.

Until the failure gate is verified, AutoSuite split requires a literal nonempty
delimiter and a literal nonnegative integer index. Runtime split selectors and
new text-list element reads/writes that require bounds guards are rejected with
`unsupported_runtime_guard`; existing numeric-list support is unchanged. Text
arrays can still be initialized, constructed, copied and passed as complete
values. The interpreter implements the full stage-2 text/list contract.

## 4. Volume and duration (A02, stage 3)

```python
from sciloom import Duration, Input, Output, Var, Volume, L, hour, mL, minute, s, uL

amount: Input[Volume]
elapsed: Var[Duration] = 0 * s
amounts: Output[list[Volume]]

# Inside @runtime; amount_ml is a declared Output[float]:
self.amount_ml = self.amount / mL
```

Volume stores canonical cubic metres; Duration stores seconds. `1 * mL` is
`1e-6` cubic metres; `1 * minute` is 60 seconds. Values are finite and exclude
Boolean-as-number. Support homogeneous lists of both quantities. Signed values
represent differences; consumers such as wait separately require nonnegative
durations. Preserve current RotationalSpeed meaning and validation.

Provide quantity construction through number-times-unit at host and runtime,
same-dimension arithmetic/comparison, scaling by numbers, ratios of like
quantities, and dividing by an explicit unit to get a number. Avoid arbitrary
dimensional algebra, offset temperatures and permissive numeric coercions.
Extend the finite scalar vocabulary; do not add an open quantity registry.

### Stage-3 representation and callable interface

Host values have keyword-only canonical constructors `Volume(m3: float)` and
`Duration(seconds: float)`. The existing `RotationalSpeed(rps: float)` remains
unchanged. `VolumeUnit` (`UL`, `ML`, `L`) and `DurationUnit` (`SECOND`, `MINUTE`,
`HOUR`) provide the root aliases above. Volume and duration support `+`, `-`,
unary signs, comparisons, numeric multiplication/division and same-kind ratios.
Division by their corresponding unit returns `float`. Wrong dimensions and
Boolean numeric arguments are errors. Unit construction works in host Python
and runtime expressions; speed construction retains its nonnegative constraint.

The new IR scalar kinds are `volume` and `duration`. Reuse `Literal` and `Binary`
instead of adding conversion nodes: `self.number * mL` becomes multiplication by
a VOLUME literal with canonical value `1e-6`; `self.amount / mL` divides by that
same typed literal and produces REAL. Constant unit literals still fold, preserving
existing speed JSON and ASFP. Numeric scaling and like-quantity ratios also apply
to speed without permitting negative speed values, speed addition or negation.

```python
from math import isclose
from sciloom import Duration, Volume, mL, minute, s, uL
from sciloom.core.ir import Binary, BinaryOp, Literal, Reference, ScalarType

assert 1 * mL == Volume(m3=1e-6)
assert isclose((1000 * uL) / mL, 1.0)
assert 1 * minute - 30 * s == Duration(seconds=30)
assert (2 * mL) / mL == 2.0

amount = Binary(
    node_id="amount", op=BinaryOp.MULTIPLY,
    left=Reference(node_id="number-ref", symbol_id="number"),
    right=Literal(node_id="one-ml", type=ScalarType.VOLUME, value=1e-6),
)
```

These interfaces are executable in stage 3. AutoSuite expressions use SI
numbers, as documented in manual 3.10.1 pp. 141–142. Floating arithmetic uses
ordinary finite real values; no exact decimal or cross-platform rounding is
promised. New quantity division requiring a
runtime nonzero check, and speed scaling requiring a runtime sign check, are
rejected until the failure-propagation gate is verified; reference execution
supports them with explicit errors. Literal nonzero divisors and provably
nonnegative speed scaling compile. This does not remove existing numeric
division support or change earlier accepted program output. New volume/duration
list indexing requiring bounds checks is likewise refused pending the failure
gate; whole-list construction, copying and parameters are available.

## 5. Numeric operations (A11, stage 4)

```python
from math import floor

# Inside @runtime with declared numeric fields:
self.magnitude = abs(self.value)
self.lower = floor(self.value)
self.nearest = round(self.value)
```

`floor(int | float) -> int`; single-argument `round(int | float) -> int` uses
Python ties-to-even. `abs` preserves numeric type and supports signed Volume and
Duration. Convert a physical quantity through an explicit unit before rounding.
Resolve the actual builtins/imported math.floor, not arbitrary functions with
matching names. No ndigits, random or blanket math-module support.

Expected: floor(-1.2) = -2; round(2.5) = 2; round(3.5) = 4;
round(-2.5) = -2. Native AutoSuite round is not presumed equivalent. A verified
arithmetic expansion is acceptable; reject unprovable target ranges. Do not
infer an integer width or floating-point equivalence from XML variable type IDs.

Stage 4 reuses `Unary(op, operand)` with stable enum values `abs`, `floor` and
`round`; no new record kind or wire-version change is needed. `abs` retains its
operand type; `floor` and `round` return INTEGER. Boolean, text, lists and
unconverted quantities cannot be rounded. `Volume` and `Duration` also implement
host `__abs__` so ordinary Python and type checkers agree with runtime source.

Source recognition uses callable identity for builtin `abs`, builtin `round` and
`math.floor`, including imported aliases. Exactly one positional argument is
accepted; a shadowing function is not executed or treated as an intrinsic.

The initial AutoSuite profile maps `abs` and real-valued `floor` to the documented
native expressions. Floor/round of INTEGER are identity operations, avoiding an
unnecessary real conversion. REAL `round` is explicitly refused with
`unsupported_rounding`: neither ties-to-even nor an equivalent expansion's
numeric range is established. No native `round` substitution or unchecked
expansion is emitted. Native numeric limits still require Executor evidence;
reference tests of large integers are not claims about vendor storage width.

## 6. Log and acknowledge (A09/A10, stages 6/7)

```python
from sciloom import log, notify

# Inside @runtime:
log(self.volume, category="recipe", stream="dispensed_volume")
notify("Samples are ready. Confirm to continue.")
```

`log(value, *, category: str, stream: str) -> None` accepts supported scalars and
quantities; category/stream can be runtime text. Capture the typed value, category
and stream once, in order. No automatic list/Zone/object formatting, device read
or application-level logging configuration. Reference events retain typed values.

Stage 6 adds `LogValue` to `sciloom.core.ir` with stable kind `LogValue` and
fields `value: Expression`, `category: Expression`, `stream: Expression`, plus
the inherited node ID/source. Value must have ScalarType; category and stream
must be TEXT. No duplicate result-type field is stored in JSON: expression
typing is authoritative. All seven current scalar/quantity types are accepted.
The operation returns no result and is only a standalone runtime statement.

```python
from sciloom.core.ir import LogValue, Literal, ScalarType

record = LogValue(
    node_id="record",
    value=Literal(node_id="amount", type=ScalarType.VOLUME, value=0.000001),
    category=Literal(node_id="category", type=ScalarType.TEXT, value="recipe"),
    stream=Literal(node_id="stream", type=ScalarType.TEXT, value="dispensed_volume"),
)
```

`sciloom.core.interpreter.LogEvent` is frozen and records `node_id: str`,
`source: SourceSpan | None`, `type: ScalarType`, `value` (a native scalar or
public quantity object), `category: str` and `stream: str`. Execution evaluates
value, category, then stream exactly once in that order, independent of keyword
spelling order, and only appends the event after all three succeed. A volume
record with canonical value 0.000001 exposes `event.value == 1 * mL` and
`event.type == ScalarType.VOLUME`. Events share the existing ordered history with
device operations. Later variable assignments do not change earlier records.

The author marker lives at `sciloom.flow.logging.log` and is lazily re-exported
as `sciloom.log`. Its Python signature accepts native bool/int/float/str and the
three current quantity classes, returning None; a host call raises TypeError.
Source analysis recognizes the marker by identity without calling it. One
positional value and the two named keywords are required; argument unpacking,
list values and use as an assignment RHS are rejected.

AutoSuite materializes all three operands in order into typed private variables,
then emits `SATaskLogData.1`. This ensures the documented Macro/variable context
even for a literal-only program. `resulttype` uses the existing scalar encoding;
text and realnumber are directly observed in the latest APP, other current types
combine the documented property-type choice with established type encodings.
Such combinations and actual persisted log content remain Executor checks;
neither an XML comparison nor a reference event claims physical measurement.

`notify(message: str) -> None` is an OK-only acknowledgement. Subsequent steps
wait for acknowledgement. Reference execution needs an explicitly configured
response; missing responses fail instead of silently confirming. No input box,
return value, cancel recovery, timeout answer or hardware I/O.

Stage 7 represents the operation as `sciloom.core.ir.Notify`, with stable kind
`Notify`, inherited ID/source and `message: Expression`. The message must be
TEXT. The author marker is `sciloom.flow.messages.notify`, lazily re-exported at
the root. One positional message or `message=...` is accepted; no argument
unpacking, extra arguments or result binding. Calling the marker on the host
raises TypeError.

```python
from sciloom.core.ir import Literal, Notify, ScalarType
from sciloom.core.interpreter import QueuedAcknowledgements, ReferenceEnvironment

statement = Notify(
    node_id="confirm",
    message=Literal(node_id="message", type=ScalarType.TEXT, value="Samples ready?"),
)
environment = ReferenceEnvironment(acknowledgements=QueuedAcknowledgements([True]))
```

Reference execution first evaluates the message once, then obtains the explicit
acknowledgement service. No service produces `missing_environment_service`;
an exhausted queue produces `acknowledgement_required`, with the requesting
node/source in both cases. It appends frozen `AcknowledgementEvent(node_id,
source, message)` only after a response was consumed. All fields are keyword-only;
source is `SourceSpan | None`, and the other fields are strings. The event joins
ExecutionEvent alongside device/log events. A later failure neither replenishes
the response nor removes earlier events. A failed run cannot resume at the
notification: another `run()` starts at the entry again, with persistent session
state. Sharing the environment or its service explicitly shares remaining
responses; omitted environments have no acknowledgement service.

QueuedAcknowledgements snapshots the iterable at construction, rejects every
entry that is not exactly True with ValueError, and tracks the remaining count.
Its acknowledge method requires text (TypeError otherwise), consumes exactly one
response on success, and raises LookupError without changing state on exhaustion.
There is no live user prompt, cancellation result, timeout or automatic approval.

AutoSuite first captures the message in one private text variable, then emits
the primary APP's `showmessage`/`ok` profile with expression mode enabled,
max wait 0, no result binding and no post-dialog pause. Zero timeout means an
unbounded wait according to manual 3.6.17. The representative UserDialog template
and F47 use okstop, and F21 uses stop: they establish the envelope, not the chosen
button policy. Only the seven observed OK tasks in the latest APP justify this
profile. Executor confirmation that later actions wait remains a separate gate.

## 7. Failure propagation (stage 8)

Ordinary external-operation failure is fatal. Explicit CSV try-operations are a
separate recoverable-result contract; no generic Python except translation.
Semantic nodes carry the operation's policy, not an AutoSuite error task.

Static checks and the reference interpreter cannot prove target termination.
Validate a minimal native failure probe in Executor with a marker task after the
failure and through a child-function call. Existing checked out-of-range reads
are only a candidate, not established proof. Logs, dialogs, flags and skipping a
body are not substitutes. Until the propagation mechanism is verified, reject
new AutoSuite programs requiring it; do not broaden that restriction into a
silent change to old accepted programs. Record the unavailable gate explicitly.

Stage 8 provides repository tooling, not a new author API or a bypass flag:

```console
uv run python autosuite/tools/probe_runtime_failure.py --output-dir /tmp/sciloom-failure-probes
```

The output directory must not exist and must not resolve inside the corpus.
It receives entry/child/loop ASFP and JSON pairs, each with an in-bounds control,
positive out-of-range read and negative-index read (nine packages). The generator
uses the existing numeric-list checked-read path; it does not weaken validation
of newly guarded capabilities or synthesize an application/deployment.

`manifest.json` records source commit and dirty-tree status, package and target
versions, hashes, generated function names, expected ordered markers and reference
diagnostics. Its Executor status is always `pending`: generation cannot promote
it to verified. Source and node IDs identify the candidate failing expression.
Package versions come from this checkout's two pyproject files, with lockstep
validation. Loaded authoring/target implementations must also resolve inside
this checkout; a foreign installation fails before output is written.
Run each package in a separate disposable APP and add an outer caller marker in
that APP. A failed child must suppress both its remaining markers and the outer
caller marker. A successful control must first demonstrate the same observation
path. Record real host results separately with the APP/re-export/log hashes.

The existing `unsupported_runtime_guard` diagnostics remain the target gate.
Stage 8 tests entry, nested and loop composition, source provenance and old v4
acceptance. There is no configuration switch accepting unverified guards. No
Executor executable is available in the current macOS checkout, so the stage
delivers the probes and enforced pending gate, not a platform-success claim.

## 8. Wall clock (A12, stage 9)

```python
from sciloom import now_text

# Inside @runtime with declared text fields:
self.stamp = now_text("%Y-%m-%d_%H%M%S")
self.output_path = self.directory + "/" + self.stamp + ".csv"
```

`now_text(format: str) -> str` reads the runtime wall clock once. The format is a
host constant; allow %Y, %m, %d, %H, %M, %S, %% and literal text only. AutoSuite
uses platform-local time; the reference environment explicitly supplies time and
zone. At 2026-09-16 14:05:06 the shown format returns `2026-09-16_140506`.
No datetime value type, locale formats, uniqueness guarantee or file-collision
handling. Wall time is separate from monotonic elapsed time.

Stage 9's author marker lives in `sciloom.flow.timing` and is lazily re-exported
from `sciloom`. It accepts one positional format or `format=`. The format may be
a literal, module/closure string constant or ordinary host-time `self` attribute;
runtime fields and arbitrary Python evaluation are not accepted. The call must
occupy the entire RHS of an assignment to one declared text field. A nested call,
discarded result, tuple/index destination or augmented assignment is rejected.

The stable IR kind is `ReadWallTime`, with `target: Reference` and `format: str`.
This is a statement, not a value expression: it cannot be duplicated or moved
while planning surrounding expressions. Shared validation checks destination
ownership/type and the format subset; dangling percent signs and other directives
are errors. Empty/literal-only formats still perform one clock read.

```python
from sciloom.core.ir import ReadWallTime, Reference

read = ReadWallTime(
    node_id="read-time",
    target=Reference(node_id="stamp-target", symbol_id="stamp"),
    format="%Y-%m-%d_%H%M%S",
)
```

The destination must be declared as TEXT in the containing FunctionIR.
ReferenceEnvironment gains `wall_clock: WallClock | None = None`, with
WallClock and VirtualWallClock exported from `sciloom.core.interpreter`.

```python
from datetime import datetime, timezone
from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualWallClock

clock = VirtualWallClock(datetime(2026, 9, 16, 14, 5, 6, tzinfo=timezone.utc))
environment = ReferenceEnvironment(wall_clock=clock)
result = Interpreter(program, environment=environment).run()
# For an output field named stamp and the ReadWallTime format above:
assert result.outputs["stamp"] == "2026-09-16_140506"
```

A missing service raises `missing_environment_service`. A failed clock read or
invalid/naive returned datetime raises `wall_clock_error` at the operation,
without writing its target or emitting a success event. No retry or second read
is attempted. Successful reads append a frozen `WallTimeEvent(node_id, source,
format, value)` after assignment; fields are keyword-only, source is optional
SourceSpan and the other fields are strings. Keeping the formatted text in the
event avoids retaining caller-owned timezone objects. Earlier completed effects
survive later failures.

The reference formatter uses explicit numeric fields rather than locale or
platform strftime behavior: month/day/hour/minute/second have two digits, year
has at least four. It uses the supplied instant's timezone without converting
to the host's timezone. VirtualWallClock accepts only aware datetimes and a bad
set leaves the prior instant unchanged. Stage 10 adds the separate monotonic
service; stage 9 introduces no placeholder timer implementation.

AutoSuite emits one Set Variable assignment whose RHS is DateTime with the
encoded constant format. Later expressions read the destination; loops/calls
execute the read where authored. Text literal/XML escaping remain separate.
Static task shape and single-evaluation scheduling do not establish Executor
formatting, local-time/DST behavior or platform calendar limits.

## 9. Wait and timer (A08, stage 10)

```python
from sciloom import Timer, s, wait

timer: Timer

# Inside @runtime:
self.timer.start()
wait(2 * s)
self.timer.wait_until(5 * s)
```

`wait(duration: Duration) -> None`; `Timer.start() -> None` resets the anchor;
`Timer.wait_until(duration: Duration) -> None` waits until that much monotonic
time has elapsed since start. Durations must be nonnegative. An already elapsed
target continues immediately; the example advances virtual time by five seconds.

Timer is a Function-owned resource, neither a device nor a Var. Extend the
resource union without changing DeviceResource's wire fields. Prove start on all
paths in the current entry invocation, not a possible earlier invocation. No
cross-Function Timer sharing initially; child execution still consumes shared
clock time. Wait never resets configuration, starts or stops equipment. No
contact/setpoint waits or timed automatic stop.

### Stage-10 concrete interfaces

The author vocabulary is `sciloom.flow.timing.Timer` and `wait`, lazily exported
from `sciloom`. A bare `timer: Timer` annotation declares a guarded, Function-owned
slot. No default, host construction, assignment, sharing, subclass or runtime
value read is supported. Inheritance may retain the same declaration but cannot
change its role. Timer calls are standalone runtime statements, accepting no
arguments for start and one positional or `duration=` argument for wait_until.
`wait` accepts the same duration argument form.

```python
from sciloom.core.ir import TimerResource, StartTimer, Wait, WaitUntil, Literal, ScalarType

timer = TimerResource(node_id="timer", owner_id="f", name="timer")
start = StartTimer(node_id="start", resource_id="timer")
pause = Wait(node_id="pause", duration=Literal(node_id="two", type=ScalarType.DURATION, value=2.0))
finish = WaitUntil(node_id="finish", resource_id="timer",
                   duration=Literal(node_id="five", type=ScalarType.DURATION, value=5.0))
# In FunctionIR f, with timer in Program.resources: elapsed reference time is 5 s.
```

Each record has the displayed stable kind. `Resource` is the closed union of
DeviceResource and TimerResource; Program.resources retains its existing wire
field. DeviceResource fields and old JSON bytes do not change. TimerResource
requires a valid owner and a distinct public name within that Function; timer
operations cannot reference another Function's timer or a device resource.
Only device resources participate in Target device binding and specialization.
Specialization removes timers whose owning Functions are pruned, while retaining
the unchanged authored program for JSON interchange and later rebinding.

`core.timing.validate_timer_usage(program) -> tuple[Diagnostic, ...]` checks a
structurally valid, specialized program. It computes definite starts and incoming
requirements across branches, zero-iteration loops and calls, then checks the
entry with an empty started set. Compiler failure uses `timer_not_started`.
Diagnostics identify each wait occurrence requiring a missing start, preserving
its path/source through call summaries rather than choosing any wait on that timer.
Reference execution checks the actual path and resets timer validity at each
entry run, so a previous run never authorizes a wait. Child calls share the entry
clock and timer state; timer IDs still belong to their own Function instances.

ReferenceEnvironment adds `clock: VirtualClock | None = None`. No service means
`missing_environment_service`, including for zero waits. VirtualClock starts at
explicit finite nonnegative seconds (default 0), has `monotonic() -> float` and
`wait(seconds: float) -> None`, rejects bool/nonfinite/negative inputs and checks
overflow before changing state. It never sleeps or changes the separate wall
clock. Runtime negative waits fail with `wait_duration`; clock failures become
`clock_error`. Arguments are captured once before waiting. Completed earlier
effects survive failure.

Successful starts emit frozen `TimerEvent(node_id, source, resource_id, started_at)`.
Successful waits emit frozen `WaitEvent(node_id, source, duration, started_at,
finished_at, timer_id)`, all keyword-only. Duration is the public Duration value;
it is an interval for Wait and the requested elapsed threshold for WaitUntil.
The times are monotonic seconds and timer_id is None for ordinary Wait. Timer
events report each reset. Events, rather than a new device-state mapping, expose
timing observations; existing device snapshots are unaffected.

AutoSuite uses SetTimer and Wait mode 0/2, SI seconds and generated unique timer
names. Its cancel-wait button is disabled so normal waits cannot silently finish
early. This option is manual-documented; its generated combination still needs
Executor verification. The observed Wait range is 0–79,999 hours. Until runtime
failure propagation is verified, durations require statically bounded literals;
negative/out-of-range values or dynamic values receive explicit target errors.

Native timers have lexical Macro scope. The first target mapping supports starts
and resets within one lexical scope per timer, with waits in that scope or its
descendants. It rejects timers whose start sites occupy different scopes or
whose wait escapes their declaration scope, rather than silently hoisting a
clock read. Core/JSON/reference semantics retain the broader Function-owned
contract, including starts in both sides of a branch followed by an outer wait.
Record this scope mapping boundary and reset/visibility checks in platform Q&A.

## 10. CSV read (A05, stage 11)

Columns are typed host descriptors whose selectors/default values may contain
runtime expressions in recognized DSL calls. Schema metadata (type/unit/count)
is static; no runtime Python Column constructor is executed during lowering.

```python
from sciloom import Function, Input, Output, Volume, csv, mL, runtime


class ReadReagentTable(Function):
    """Read a reagent column after the experiment-ID column."""

    path: Input[str]
    reagent_index: Input[int]
    reagent_name: Output[str]
    ids: Output[list[str]]
    volumes: Output[list[Volume]]

    @runtime
    def run(self) -> None:
        self.reagent_name, = csv.read_row(
            self.path,
            row=0,
            header=False,
            columns=(csv.Column(index=self.reagent_index + 1, value_type=str),),
        )
        self.ids, self.volumes = csv.read_columns(
            self.path,
            header=True,
            columns=(
                csv.Column(index=0, value_type=str, default=""),
                csv.Column(index=self.reagent_index + 1, value_type=Volume,
                           unit=mL, default=0 * mL),
            ),
        )
```

`reagent_index` is zero-based **within the reagent columns**, excluding the
experiment-ID column at CSV index 0. Thus reagent_index=0 selects CSV column 1,
the first reagent. The `+ 1` skips that ID column; it is not conversion to vendor
indexing. A caller already holding an absolute zero-based CSV column index passes
that index directly. Only the backend converts to AutoSuite's one-based indexes.

The call contract is:

```text
csv.Column(*, index, value_type, unit=..., default=...)
csv.read_row(path, *, row, header, columns)
csv.read_columns(path, *, header, columns)
csv.try_read_row(path, *, row, header, columns)
csv.try_read_columns(path, *, header, columns)
```

Here `...` in the displayed signature means an **omitted argument**, not an
accepted Ellipsis value. Index/row are nonnegative integers excluding bool;
path is str; header is a host bool. Columns is a nonempty, statically sized tuple.
Support selected supported scalars, not Zone. Quantities require an explicit
matching column unit; omit unit for ordinary scalar columns. Type-check defaults
against the result type using the existing literal widening rule. Capture path,
selectors and defaults once before reading. The initial delimiter profile is the
observed comma mode; do not expose unverified vendor numeric enum values.

Read-row returns a tuple of scalar results; read-columns returns a tuple of
independent homogeneous lists. One column still returns a tuple. Bind every
result to an existing distinct field. Public row/column indices are zero-based;
header=True indexes data after the header. The backend converts vendor indexing.
Empty data gives empty column lists; a nonexistent selected row is EOF. Preserve
alignment across all selected columns, including defaulted cells.

For example, the file `ID,volume\nA,1.5\nB,\n`, read with header=True and columns
text/Volume in mL with a zero default, produces `("A", "B")` and quantities
`(1.5 * mL, 0 * mL)` in immutable reference snapshots.

Default policy: fail unless a column explicitly supplies a default for missing
cells or conversion failures. A column default does not recover a file error.
Try calls prepend exactly one integer status to a **flat** result tuple:
`(status, value0, ..., valueN)` for try_read_row and
`(status, list0, ..., listN)` for try_read_columns. A one-column result is
`(status, value)` or `(status, values)`, not a nested results tuple. Expose
`csv.OK = 0`, `csv.DEFAULT_USED = 1`, `csv.EOF = 2`, `csv.INVALID_DATA = 3`,
`csv.IO_ERROR = 4`. These are SciLoom statuses, not raw vendor result codes.

Aggregate outcomes in this priority order, highest first:
IO_ERROR, EOF, INVALID_DATA, DEFAULT_USED, OK. EOF means a requested single row
does not exist; natural exhaustion of an all-row read is successful completion,
including an empty dataset. A converted/defaulted cell contributes DEFAULT_USED;
an unhandled missing/bad cell or malformed record contributes INVALID_DATA. A
file failure contributes IO_ERROR even after some cells were read. Column
defaults recover only their own cell problems, never a whole-file failure.
Invalid selectors, declaration errors and wrong-typed defaults remain programming
errors rather than recoverable CSV statuses.

Try-read-row requires a default on every column. With OK/DEFAULT_USED it returns
the accepted values; on IO_ERROR/EOF/INVALID_DATA it returns **all** captured
column defaults, never a mixture of partial values and fallback results.
Try-read-columns returns all accepted lists on OK/DEFAULT_USED and **all empty
lists** on whole-operation failure. Both try forms commit the status and the
chosen complete payload together. Ordinary reads commit no result destinations
on failure; accepted success commits them together. Do not promise a filesystem
transaction or snapshot against other writers. Preserve earlier effects.

For two selected columns, one defaulted cell plus one unhandled bad cell in an
all-row read yields `(csv.INVALID_DATA, [], [])`; a later file failure instead
yields `(csv.IO_ERROR, [], [])`. A missing requested row with defaults `""` and
`0 * mL` yields `(csv.EOF, "", 0 * mL)`. These payload examples use author-level
list notation; reference result snapshots continue to expose lists as tuples.

Retain a typed CSV-read node with mode, columns, error policy and outputs. Backend
private tasks may read/check separately; an aggregate vendor status is not proof
of per-column validation. Establish unit/default conversion and cell-expression
behavior separately; never eval CSV content as Python. Tests must not silently
equate the vendor parser to Python's CSV dialect or numeric conversion rules.
Mypy checks column/default types where expressible; SciLoom checks arbitrary-width
result bindings. Do not add a plugin or one overload per tuple width.

### Stage-11 concrete records and parsing profile

These additions are implemented in the stage-11 branch for reference execution;
AutoSuite compilation remains gated. The public declarations live in `sciloom.flow.csv`, lazily
exported as `sciloom.csv`. `Column[T]` is a frozen keyword-only generic descriptor
with `index: int`, `value_type: type[T]`, an optional physical unit and an optional
typed default. Omission has its own sentinel; None is not a valid default. The
four read markers return `tuple[Any, ...]` because their heterogeneous width is
defined by Column metadata; SciLoom, not mypy, validates every result binding.
Calls only occupy an entire tuple-unpacking assignment RHS, even for one result.
Column calls are inline metadata in `columns=(...)`; source analysis does not
execute their constructors, selectors or defaults.

IR constructors are exported from `sciloom.core.ir`:

```python
from sciloom.core.ir import (
    CsvColumn, CsvErrorPolicy, CsvReadMode, Literal, ReadCsv, Reference, ScalarType,
)

read = ReadCsv(
    node_id="read", mode=CsvReadMode.ROW, error_policy=CsvErrorPolicy.RAISE,
    path=Literal(node_id="path", type=ScalarType.TEXT, value="recipe.csv"),
    header=False,
    row=Literal(node_id="row", type=ScalarType.INTEGER, value=0),
    columns=(CsvColumn(
        index=Literal(node_id="column", type=ScalarType.INTEGER, value=0),
        type=ScalarType.TEXT,
    ),),
    targets=(Reference(node_id="target", symbol_id="name"),),
)
```

`CsvReadMode` uses `ROW="row"` and `COLUMNS="columns"`;
`CsvErrorPolicy` uses `RAISE="raise"` and `STATUS="status"`. ReadCsv has one
path expression, a host Boolean header flag, an optional row (required for ROW,
absent for COLUMNS), nonempty typed columns and distinct ordered target references.
STATUS prepends an INTEGER target. Each CsvColumn has an index expression, scalar
type, optional `unit: Literal` and optional default expression. A unit is a finite
positive quantity literal representing one input unit in canonical SI, matching
the column type. Defaults are already typed canonical values, not rescaled.
No Python unit object or vendor parameter is serialized.

The reference CSV profile is UTF-8 (an initial UTF-8 BOM is accepted), comma
delimited, double-quoted with doubled quote escapes, LF or CRLF records, and
quoted embedded line breaks. Parsing uses Python's strict CSV reader explicitly
as the reference profile, not as proof of AutoSuite equivalence. A blank physical
record contains no cells; empty input contains no records. Header handling skips
one parsed record. Row mode parses through its selected record; later records
are outside that selection, but decoding validates UTF-8 across the whole file.
Column mode validates the entire input. The reference parser retains Python's
CSV field-size limit and reports parser-limit failures as INVALID_DATA.

Text cells preserve parsed text. Numeric conversion trims only space/tab/CR/LF,
accepts ASCII decimal integers or decimal/exponent real syntax, rejects empty
cells, nonfinite values, expressions, underscores, hexadecimal and fractional
integers. Boolean cells accept `true` or `false`, case-insensitively after that
same trimming; no implicit numeric Boolean conversion. Quantities use finite
decimal numbers times the declared unit; speed also requires nonnegative values.
Missing or invalid cells use only their own explicit defaults. Invalid UTF-8 and
malformed records produce INVALID_DATA for the operation, not per-cell defaults.

ReferenceEnvironment adds `files: FileService | None = None`, with the byte
adapters in section 2. One read captures path, row, then each column index/default
in declaration order before calling read_bytes exactly once. File OSError gives
IO_ERROR; invalid path/selector arguments are programming errors. No implicit
local file adapter is selected. LocalFiles validates containment before access;
it is not a security sandbox against concurrent filesystem changes.

`CsvReadEvent` is a frozen keyword-only record exported by `core.interpreter`:
`node_id`, `source`, `path`, `mode`, `header`, `row`, `columns: tuple[int, ...]`
and `status: int`. A completed read attempt records its outcome, including a
CSV failure, before either committing all outputs or raising. Missing services
and invalid arguments do not create read events. Events do not duplicate file
bytes or result arrays. Status-form errors commit complete fallback payloads;
ordinary errors emit the outcome event but change no destination fields.

AutoSuite's manual explicitly evaluates cell expressions and truncates real
cells assigned to integers. Its aggregate result does not specify mixed-column
precedence. Therefore native CSV tasks are not automatically equivalent to this
reference profile. Ordinary reads also need the still-unverified fatal-error
gate. Implement and test the supplied task envelope and bounded probes separately;
Target must reject unsupported parsing/status/failure semantics rather than emit
a file that claims full ReadCsv behavior. Record profile and Executor gaps in
the evidence matrix and Q&A; a successful reference recipe is not vendor acceptance.

## 11. CSV append (A06, stage 12)

```python
from sciloom import csv

# Inside @runtime:
csv.append_row(self.output_path, values=(self.log_line,))
self.status = csv.try_append_row(self.output_path, values=(self.log_line,))
```

`append_row(path: str, *, values: tuple[...]) -> None` captures values and writes
one ordered row; its try counterpart returns integer OK/IO_ERROR. The tuple is
nonempty and statically sized. IR retains its ordered, typed column structure.
AutoSuite initially accepts the observed **one text column** profile; reject
other types/widths until separately verified. No append method on runtime lists.

No automatic parent-directory creation, retry, rollback, header generation,
overwrite, change-cell or multiple-array-row export. Verify repeated writes,
new-file behavior, quoting and embedded line breaks. Logical records/units are
portable contracts; encoding and physical newline behavior are platform profiles.

### Stage-12 concrete append contract

The following is the implementation contract recorded before stage-12 code.
It becomes executable in stage 12; native AutoSuite acceptance remains subject
to the evidence gate below.

```python
from sciloom import csv
from sciloom.core.ir import AppendCsv, CsvErrorPolicy, Literal, Reference, ScalarType

# Inside @runtime, after declaring path, line and status fields:
# csv.append_row(self.path, values=(self.line,))
# self.status = csv.try_append_row(self.path, values=(self.line,))

append = AppendCsv(
    node_id="append",
    path=Literal(node_id="path", type=ScalarType.TEXT, value="log.csv"),
    values=(Literal(node_id="line", type=ScalarType.TEXT, value="sample A"),),
    error_policy=CsvErrorPolicy.STATUS,
    status=Reference(node_id="result", symbol_id="status"),
)
```

AppendCsv is a frozen Node with stable `__ir_kind__="AppendCsv"`, path Expression,
nonempty ordered `values: tuple[Expression, ...]`, CsvErrorPolicy and optional
`status: Reference`. RAISE forbids a status destination; STATUS requires INTEGER.
Column types come from their expressions and symbol declarations, without a
second manual type directory. All current scalars and quantities are reference
values; lists, Zone and arbitrary objects are not. The author markers accept
`tuple[int | float | bool | str | RotationalSpeed | Volume | Duration, ...]`;
normal append returns None and must stand alone, try-append returns int and must
occupy a whole single-field assignment RHS.

Capture path and each value left-to-right exactly once, then serialize one record
before accessing the file service. The reference output profile is UTF-8 without
BOM, comma-delimited, doubled double quotes with minimal quoting, CRLF record
termination. Text is literal, booleans use lowercase true/false, integers decimal,
finite real values Python round-trippable decimal text. Quantities use canonical
SI numbers (m³, seconds, rotations per second), not display-unit strings. Reading
those quantity cells requires the corresponding unit explicitly. There is no
automatic number-to-text conversion elsewhere in the language.

The operation appends the encoded record verbatim. It does not inspect, repair
or insert a missing terminator into existing bytes; a caller-owned existing CSV
must already end at a complete record boundary. No existing-content validation,
new header, overwrite, parent-directory creation, retry or rollback is implied.

Reference execution requires the same explicit FileService as reads. OSError
produces IO_ERROR; ordinary append then raises csv_io_error, while try-append
writes the status and continues. A successful write returns OK. Invalid arguments,
unencodable text, missing services and unexpected provider errors stay fatal,
not IO_ERROR. The built-in dedicated path-validation exception maps to csv_path;
other provider exceptions or non-None append return values map to file_service_error.
An adapter may have written a prefix before failing; do not erase or invent a
rollback of those bytes.

`CsvAppendEvent` is a frozen keyword-only record exported by core.interpreter,
with node_id/source/path, `types: tuple[ScalarType, ...]`,
`values: tuple[InputScalar, ...]` and integer status. It records completed write
attempts, including IO_ERROR, before raising or returning status. Values are the
captured requested logical row, not a claim that all bytes reached the file.
Invalid arguments/encoding, absent services and faulty providers create no event.

The audit established only one native Export CSV profile: delimiter/endline/
exportbehaviour/multiplelines all 0, one text column. Manual §3.7.9 specifies native
0 success and 1 IO error but does not tie numeric export-mode enums to labels.
F46's repeated logging suggests append; it does not prove that mode 0 cannot
overwrite. Therefore isolate observed native task generation in measurement
probes until repeated-write/new-file results establish append semantics. Ordinary
append also needs the fatal-error gate; quote/encoding/line endings need their
own measurements. Target must reject unsupported native append semantics instead
of assuming a potentially destructive export mode. No silent bypass is added.

## 12. Zone values and directory (A03, stage 13)

```python
from sciloom import Function, Input, Output, Var, Zone, runtime, zones


class ResolveLocation(Function):
    """Resolve the caller's name in the configured location directory."""

    zone_name: Input[str]
    selected: Output[Zone]
    scratch: Var[Zone] = Zone.empty()

    @runtime
    def run(self) -> None:
        self.selected = zones.find(self.zone_name)
```

Zone is an immutable ordered set of unique well references. It has its own value
type and literal representation; do not add it to list element/scalar-numeric
rules accidentally. Permit empty initial state, inputs, outputs, assignment,
function calls, `len(zone)`, `zones.find(name: str) -> Zone`,
`zones.combine(left: Zone, right: Zone) -> Zone`, and
`zones.well_name(value: Zone) -> str` for exactly one well. Combine preserves first
occurrence order. Unknown names find an empty Zone; well_name rejects empty or
multi-well values. Lookup uses a fixed directory, not host-global configuration.

No list[Zone], truthiness, raw integer-to-well conversion or implicit expansion.
Well identity is not its position in a Zone. Core uses opaque well identities;
AutoSuite translates deployment-specific IDs and ancestry.

`AutoSuiteLayout.from_app(path: str | Path) -> AutoSuiteLayout` reads gzip APP XML
without modifying it. Extract only required zone/well/device relationships,
preserving the verified enumeration order. No task import, APP writing or
application compilation. Device selection below uses this same read-only layout.

### Stage-13 concrete values and directory

The following interfaces were recorded before implementation and are runnable
in stage 13, verified by the Zone author/developer examples and tests.
`Zone` is a frozen, keyword-only data value in `sciloom.core.locations`,
lazily exported by `sciloom`. `Zone(well_ids: tuple[str, ...] = ())` requires unique,
nonempty opaque identities and owns an immutable tuple. `Zone.empty()` returns an
empty value; host `len()` is available and `bool(zone)` raises TypeError. Runtime
indexing/traversal wait for stage 14. A well identity is never its integer position
in a Zone; consumers cannot infer hardware from its spelling.

```python
from sciloom import Zone
from sciloom.core.locations import LocationDirectory, Well
from sciloom.core.interpreter import ReferenceEnvironment

directory = LocationDirectory(
    wells=(Well(identity="rack:a", name="Rack: Well #0"),
           Well(identity="rack:b", name="Rack: Well #1")),
    zones={"rack": Zone(well_ids=("rack:a", "rack:b")),
           "first": Zone(well_ids=("rack:a",))},
)
assert directory.find("rack").well_ids == ("rack:a", "rack:b")
assert directory.find("missing") == Zone.empty()
assert directory.well_name(directory.find("first")) == "Rack: Well #0"
environment = ReferenceEnvironment(locations=directory)
```

Well and LocationDirectory are frozen keyword-only core data records. Well has
`identity: str` and `name: str`. Directory accepts `wells: tuple[Well, ...]` and
`zones: Mapping[str, Zone]`, copies/freeze-protects its mappings, and rejects
duplicate identities, empty names, unknown membership and wrong value types.
`find(name: str) -> Zone` and `well_name(value: Zone) -> str` are deterministic
queries. The latter requires one known well. An explicitly supplied directory
may be shared between sessions because it cannot change. Omitted directories
cause missing_environment_service only when a lookup/name query needs one.
Zone assignment, passing, combining and length need no external directory; using
opaque values does not itself assert that a deployment contains those wells.

`sciloom.flow.zones` supplies the root `zones` runtime markers `find`, `combine`
and `well_name` with the signatures above (`combine(left: Zone, right: Zone) -> Zone`).
They are analyzed without executing host calls. Zone.empty() is also recognized
as a constant runtime expression. Combine retains left order then unseen right
members. Runtime arithmetic, comparison and truthiness remain unsupported.

IR uses a separate frozen `ZoneType` (stable kind ZoneType, diagnostic value
`zone`), alongside ScalarType and ListType. It is not a list element type. Add
frozen expression nodes with matching stable kinds: ZoneLiteral(well_ids tuple),
ZoneFind(name Expression), ZoneCombine(left/right Expression), ZoneLength(value
Expression) and WellName(value Expression). Variable.initial accepts ZoneLiteral;
old fields/kinds and canonical JSON remain unchanged. Runtime values and result
snapshots use immutable Zone values, not tuples that could be mistaken for lists.
Schema/default, expression, codec, interpreter, specializer and target consumers
all handle or explicitly reject these values. Log/CSV scalar rules exclude Zone.

The target exports immutable `AutoSuiteElement(identity, name, type_id, device_id,
parent_id)` and `AutoSuiteWell(identity, element_id, well_id)` records, and
`AutoSuiteLayout(elements, wells, directory)`, all keyword-only. Its
`from_app(path: str | Path) -> AutoSuiteLayout` classmethod reads only gzip APP
configuration and zones. Element identity is its normalized XML UUID; opaque well
identity derives from that element identity and the element-local well ID. Zone
references resolve the observed `(progID, deviceID, id)` triple; ambiguous or
missing references are errors. Parent links retain the actual element tree, not
a guessed relation based on matching names.

The current APP enumerates explicit well `index` values consecutively from zero;
preserve that order and validate completeness/uniqueness. Do not sort by local
well ID, element ID or display name. Accept the observed ordinary-zone profile
(virtualVial=0, enumerationType=0); other profiles are explicit layout errors.
Read all well records for membership validation, including wells absent from a
named zone. Display labels use the documented parent-name / `Well #ID` format.
Unknown profiles, unresolved references and malformed gzip/XML do not silently
produce a partial layout. No layout import mutates the APP or imports tasks.

Stage-13 AutoSuite supports zone parameters, empty initial state, assignment,
function passing, FindZone, ZoneSize and documented zone addition where the
profile can preserve semantics. Nonempty opaque Zone literals have no established
general XML expression mapping and are rejected explicitly. A runtime WellName
query needs single-well validation; until the failure gate is verified, reject
unproven cardinality rather than emitting an unchecked native call. Record
enumeration/name/combination execution checks separately from static XML evidence.
Existing fixed equipment profiles remain unchanged. Selection bindings, at()
scopes and physical state tracking are not added ahead of stage 16.

## 13. Zone traversal (A04, stage 14)

```python
from sciloom import Function, Input, Output, Var, Zone, runtime, zones


class CountRack(Function):
    """Count wells and pairs in a rack with an even number of wells."""

    rack: Input[Zone]
    well: Var[Zone] = Zone.empty()
    fragment: Var[Zone] = Zone.empty()
    well_count: Output[int]
    pair_count: Output[int]

    @runtime
    def run(self) -> None:
        self.well_count = 0
        self.pair_count = 0
        if len(self.rack) > 0:
            self.well = self.rack[0]
        for self.well in self.rack:
            self.well_count += 1
        for self.fragment in zones.fragments(self.rack, size=2):
            self.pair_count += 1
```

This complete Function becomes runnable in stage 14, without a stage-15 property
dependency. Four wells produce well_count=4 and pair_count=2; an empty rack gives
both counts zero. Loop targets are declared Var[Zone] fields. Capture the iterable
once. Index reads accept nonnegative non-bool ints
and reject bounds failures. Fragment size is a positive host int. Empty zones
skip; nonempty cardinality must be divisible by the size, with no short tail.
Validate these conditions before body effects. Exclude multi-zone/batch traversal,
break, continue and for/else. Preserve a ForEachZone-style high-level node and
map it to the observed sequential macro, whose fragment position is distinct
from the ordinary loop counter. Apply normal zero-iteration analysis.

## 14. Well properties (A07, stage 15)

```python
from sciloom import WellProperty

def __init__(self):
    self.sample_label = WellProperty("sample_ID", str)

# Inside @runtime:
self.sample_label[self.well] = self.label
self.previous = self.sample_label.get(self.well, default="")
```

`WellProperty(name: str, value_type: type[str])` is a host descriptor;
`get(zone: Zone, *, default=...) -> str` is an ordered runtime read, and indexed
assignment is an ordered runtime write. Name and type are static. First support
text user properties only. Read exactly one well; missing/wrong-type data fails
unless a default is explicitly supplied. Writes capture one value and assign it
to all selected wells. An empty write affects no wells. Property stores key by
well identity. This is metadata, not a configured device getter or measurement.
No per-well array write, native read-only measured properties or arbitrary getter.

## 15. Dynamic device location (A03, stage 16)

```python
from sciloom import Agitator, Function, Input, RotationalSpeed, Zone, at, runtime, s, wait
from sciloom_autosuite import (
    AutoSuiteAgitatorSelection,
    AutoSuiteIndividualShaker,
    AutoSuiteLayout,
    AutoSuiteTarget,
)


class StirSelected(Function):
    """Stir a caller-selected compatible location, then stop it."""

    agitator: Agitator
    location: Input[Zone]
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        with at(self.agitator, self.location):
            self.agitator.speed = self.speed
            self.agitator.start()
            wait(5 * s)
            self.agitator.stop()


target = AutoSuiteTarget(
    layout=AutoSuiteLayout.from_app("configuration.app"),
    devices={
        "agitator": AutoSuiteAgitatorSelection(candidates=(
            AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
            AutoSuiteIndividualShaker(zone="Heater Shaker 24", device_id="24"),
        )),
    },
)
StirSelected().compile(target=target).write("stir_selected.asfp")
```

`at(device, location: Zone)` is a recognized lexical runtime scope. Entry captures
the location once and checks it before body effects. Exit does **not** stop the
device or restore an earlier physical state. Reject same-device nested selection;
different devices can nest. Calls using a shared logical reference inherit the
selection, passed through backend-private context. A dynamically bound device
operation outside a provable selection scope fails; fixed bindings keep working.

AutoSuiteAgitatorSelection has a nonempty immutable candidate tuple, each with
the same concrete contract in this first profile. Validate candidate well/device
ancestry from layout; a selection must be a nonempty subset of one candidate's
allowed wells and belong to exactly one compatible physical controller. Reject
unknown/out-of-range selections and zones spanning controllers. Compare well
identities, not just names; rack and shaker IDs are not interchangeable.

Different logical resources cannot have overlapping physical candidate sets;
share the logical reference intentionally. Core adds a data-only selection
binding without changing DeviceBinding's single-controller meaning. Target
resolve_devices still runs once; specialization queries use the common candidate
contract, never a guessed runtime choice. No implementations load from JSON.

Saved configuration belongs to the logical resource and persists within a
session; start applies it to the selected physical controller. Stop affects the
selected controller only and preserves saved/applied configuration. Selecting
another controller does not stop the first. Prove required configuration across
calls and all paths of the current entry, without assuming historical calls.

Keep existing logical resource snapshots as saved configuration / last action.
Add `ExecutionResult.physical_devices` keyed by physical identity, with applied
configuration and enabled state; add selected physical identity to relevant
events without changing old program behavior. A reference environment provides
trusted selection facts. Backend shared configuration and active selection are
private parameters, with normal-return propagation as before; abnormal recovery
equivalence remains an explicitly unverified question.

## 16. Target extension boundary (current protocol, all stages)

Keep `target_id`, `resolve_devices(program) -> DeviceBindings`,
`validate(program) -> tuple[Diagnostic, ...]`, and `emit(program) -> Artifact`.
No target discovery or compulsory namespace installation. The current independent
[demo contribution](../../../examples/developer/demo_contribution/__init__.py)
shows property/command extension without core changes.

A deliberately device-free inspection target using the current protocol:

```python
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import Program, to_json


class JsonInspectionTarget:
    target_id = "example.json-inspection/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return DeviceBindings()

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return ()

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode("utf-8"),
                        media_type="application/json", suffix=".json")


# With an already-built valid, device-free, specialized Program:
result = compile_ir(program, target=JsonInspectionTarget())
assert result.artifact.content == to_json(program).encode("utf-8")
```

This target serializes for inspection; it does not execute operations or claim
hardware support. Generic compilation rejects missing device bindings. An actual
equipment target must reject unsupported selected operations/types explicitly.
CompileResult.semantic_ir stays authored; specialized_ir stays high-level;
backend-private checks, temporaries and XML identifiers enter neither one.

## Version

Version: none, this is the stage-0 design contract. The accepted sequence keeps
JSON v4, moves both packages to 0.3.0 at stage 1, and uses lockstep 0.3.x afterward.
No release tag, PyPI publication or 1.0.0 bump.
