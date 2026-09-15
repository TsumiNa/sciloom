# Runtime capability interface contract

## Status and ownership

This is the authority for the [implementation sequence](00-overview.md). All new
signatures and snippets below are **target interfaces** until their stated stage
lands. They have not been executed. Existing Program/JSON v4, Function.compile,
device property/command contracts and the Target protocol are current.

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
are captured once at operation entry. Multi-result destinations are distinct
fields; commit results together after the operation accepts them. A failure does
not roll back earlier state changes, device actions or file writes.

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
ReferenceEnvironment implementation/service signatures are recorded here by
stage 5 before its API is added; no absent service is exposed as a placeholder.

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

`notify(message: str) -> None` is an OK-only acknowledgement. Subsequent steps
wait for acknowledgement. Reference execution needs an explicitly configured
response; missing responses fail instead of silently confirming. No input box,
return value, cancel recovery, timeout answer or hardware I/O.

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

## 10. CSV read (A05, stage 11)

Columns are typed host descriptors whose selectors/default values may contain
runtime expressions in recognized DSL calls. Schema metadata (type/unit/count)
is static; no runtime Python Column constructor is executed during lowering.

```python
from sciloom import Volume, csv, mL

# Inside @runtime with declared output fields:
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
Try calls prepend an integer status; expose `csv.OK`, `csv.DEFAULT_USED`,
`csv.EOF`, `csv.INVALID_DATA`, `csv.IO_ERROR` as named integer constants. Their
meaning is SciLoom's, not the raw vendor result code. Successful default use is
DEFAULT_USED; an unhandled bad/missing cell is INVALID_DATA. A file failure is
IO_ERROR; a requested row beyond data is EOF.

Try-read-row requires a default on every column so whole-operation failure has
well-typed results. Try-read-columns returns empty lists on whole-operation
failure. Normal failure commits no result destinations; accepted success commits
them together. Do not promise a filesystem transaction or snapshot against other
writers. Preserve effects completed before the operation.

Retain a typed CSV-read node with mode, columns, error policy and outputs. Backend
private tasks may read/check separately; an aggregate vendor status is not proof
of per-column validation. Establish unit/default conversion and cell-expression
behavior separately; never eval CSV content as Python. Tests must not silently
equate the vendor parser to Python's CSV dialect or numeric conversion rules.
Mypy checks column/default types where expressible; SciLoom checks arbitrary-width
result bindings. Do not add a plugin or one overload per tuple width.

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

## 12. Zone values and directory (A03, stage 13)

```python
from sciloom import Input, Output, Var, Zone, zones

location: Input[Zone]
selected: Output[Zone]
scratch: Var[Zone] = Zone.empty()

# Inside @runtime:
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

## 13. Zone traversal (A04, stage 14)

```python
well: Var[Zone] = Zone.empty()
fragment: Var[Zone] = Zone.empty()

# Inside @runtime; the property write becomes available in stage 15:
self.well = self.rack[0]
for self.well in self.rack:
    self.sample_label[self.well] = self.label
for self.fragment in zones.fragments(self.rack, size=2):
    self.sample_label[self.fragment] = self.label
```

Stage-14 tests use already-supported operations in the body; the displayed
property example runs only after stage 15. Loop targets are declared Var[Zone]
fields. Capture the iterable once. Index reads accept nonnegative non-bool ints
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
