# Runtime list mapping and evidence

SciLoom's AutoSuite 2.47.1.1 target compiles homogeneous one-dimensional lists.
The semantic contract lives in
[the package refactor](../../docs/refactor/package-layout/00-overview.md).
The original evidence below is unchanged; generated examples live under `examples/`.

| Construct | Emission | Evidence / confidence |
|---|---|---|
| Array declaration | `values/count`, indexed `valueN/type/value`, outer `type`, units, `array=1` | Latest APP and extracted main; original Suzuki-Miyaura application for integer and dimensionless real arrays |
| Element storage | 3 integer, 5 real/physical, 11 bool | Scalar codes observed; integer/real arrays observed; bool-array combination is derived from scalar wire format and manual array semantics |
| Parameters | Element `variabletype`, `isarray=1` | Latest APP / `51_Non Zero Array Min.asfp` uses volume-array input |
| Length/read | `ArraySize(name)` and `name[index]` | `51_Non Zero Array Min.asfp` and `31_Get Aspirate Chunk.asfp` |
| Indexed write | Set Variable: whole `variablename`, mode 0, `elementnumber`, element expression | `44_Set ISynth Drawer State.asfp`, `g_drawer_state` assignment |
| Whole-array assignment | Set Variable mode 4; source array name as expression | `config20260902_2.app`, task manager's array_vol assignment from g_array_vol |
| Array call input | `variablename` binding, empty `expression` | Latest APP / `30_Dynamic Transfer Volumectrically.asfp`; 142 observed array-input call bindings use this form |
| Physical array | Scalar angularspeed encoding plus array flags/values | Derived composition: scalar angularspeed evidence in [agitation mapping](16_AGITATION_MAPPING.md), physical volume arrays in latest APP |

Array initialization retains an explicit count, including zero. Integer arrays use
dimensionless `unit=1` as observed in Suzuki-Miyaura. Boolean defaults encode true
as -1; rotational speeds are canonical revolutions/second with rpm as display unit.
The Boolean and rotational-speed array combinations require Executor confirmation.

## Copying, construction and function boundaries

Whole-array Set Variable is used for value copies. Every array input is copied
into private working storage on function entry, including externally invoked
functions. Every array output uses separate working storage and copies out on
return. Calls additionally bind private input/output arrays, preventing vendor
parameter aliasing from connecting SciLoom variables. These combinations have
static and test-model coverage; vendor parameter alias behavior is not established.

Literal construction allocates a private array of the known length, initialized
with typed zeros, and writes each element in expression-evaluation order on every
evaluation. Empty literals use private empty arrays. These buffers are never
resized or passed directly as mutable call parameters. No Python literal string
is emitted into AutoSuite's expression language.

To avoid reusing stale vendor output storage, the target conservatively requires
whole-list output assignment on every return path and before any read. Both If
branches must assign; a possibly-zero-iteration While cannot establish definite
assignment. Unsupported cases report `list_output_initialization`. This is a
target restriction, not a change to the reference interpreter's runtime errors.

## Checked indices and expression scheduling

Manual 3.8.5 (printed pages 113–116) establishes homogeneous, zero-based arrays and
an error when reading beyond the upper bound. Indexed writes can grow arrays;
SciLoom's indexed updates must not use that behavior.

The backend captures an index once. If negative, it replaces it with the array's
length, then executes a scalar read of that element. This is intended to trigger
the documented upper-bound error before a write can grow the array. Nonnegative
out-of-range indices use the same read. Actual fatal propagation remains
unverified; [the failure gate](24_RUNTIME_FAILURE_GATE.md) supplies control and
failure probes. No negative wrapping or successful termination check is assumed.

Expressions return ordered prerequisite tasks plus their value expression. Plain
indexed assignment evaluates the right side before checking the destination;
augmented assignment checks/reads the destination before its right side. Earlier
binary operands and call arguments are captured before later prerequisite tasks.
While conditions with checks are evaluated once before entry and again at the
tail of every iteration, each with distinct task IDs. If checks remain inside
the selected outer branch. No check is treated as a disposable calculation.

The combined fault/guard sequence is **derived**, not a captured vendor-exported
probe. Executor must confirm that a faulting read aborts before the indexed write,
including nested conditions, physical/bool arrays and repeated calls. The test-only
wire model intentionally aliases parameter arrays and grows unchecked writes to
exercise isolation/guard scheduling; it is not an AutoSuite emulator or simulator.

## Learning examples and deferred behavior

[non_zero_array_min.py](../../examples/non_zero_array_min.py) adapts the latest
APP's `Non Zero Array Min`: remove volume units, retain numeric threshold 1e-8
and sentinel 999999, and express the conjunction with nested If statements.
This is a dimensionless algorithm demonstration, not physical volume equivalence.
[scale_values.py](../../examples/scale_values.py) demonstrates copies and updates.
Both have complete generated ASFP companions and reference-execution tests.

The original CSV header importer and Suzuki-Miyaura workflows construct arrays
through CSV and growing indexed writes. This is a future explicit construction
requirement, not permission for SciLoom indexed assignment to resize. No explicit
append/pop/remove/clear method usage was observed in the raw corpus. Manual
references to array editing do not establish the missing wire mappings.

Real integration remains open: insert generated functions into a matching known
application and run `AutoSuiteExecutor.exe ... /r /sim 100 /s /c` on the AutoSuite
host. XML parsing, corpus comparisons and the wire test model do not satisfy that gate.
