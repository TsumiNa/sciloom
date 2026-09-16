# Zone indexing and sequential traversal

Stage 14 adds ZoneGet and ForEachZone to the existing JSON v4 contract. The
reference implementation covers indices and complete groups. AutoSuite emits
single-well sequential macros; guarded index/group operations remain unavailable
until [runtime failure propagation](24_RUNTIME_FAILURE_GATE.md) is verified.

## Evidence and implementation

| Construct | Original XML evidence | Manual semantics | Reference execution | Executor status |
| --- | --- | --- | --- | --- |
| Single-well traversal | F46 `Export Wells Log`: executionmode=1; count=1; fragmentsize=1; macro-local well_zone sourced from wells_zone | 3.8.10–12, printed pp. 121–126: sequential Zone is current fragment | Captured order, current-well assignment and persistence tested | Pending order, capture and repeated-call checks |
| Complete groups | Same native record has fragmentsize; F43 also uses size 1 | Printed pp. 122–125: total wells must be a multiple of fragment size; eight wells/size two yields four cycles | Positive static size; reject remainder before any target/body write | Native groups >1 rejected pending reliable failure propagation |
| Index lookup | F43 `Get Well Zone With Index`: validate well_idx, enumerate size-one Zone, compare fragment variable frag to well_idx, assign single_zone to output | Zone is ordered; sequential fragment is distinct from the loop counter | Exact integer, nonnegative bounds; result is a one-well Zone | Native indexing rejected; custom Error Handler call is not evidence of fatal propagation |
| Empty selection | No explicit empty-case proof in F43/F46 | Reviewed sequential-macro pages do not establish empty behavior | Zero iterations, preserve prior target | Generated outer If skips the entire sequential macro; Executor still pending |
| Nested iteration | Macro nesting and independent local variable containers | Nested sequential Zones are described using enclosing fragments as input | Independent captures, including reused semantic targets | Pending scope/copy behavior on deployment |

F43/F46 refer to unchanged files under
`autosuite/corpus/extracted/latest_app/functions/`. No evidence file is rewritten
or published. The native XML is compared structurally, not treated as an executed
test. Well IDs such as 27 are identities, not zero-based selection positions.

## Native scheduling

1. Evaluate and copy the iterable into a private Zone variable once.
2. Test `ZoneSize(captured) > 0` in a separate outer conditional Macro. The
   sequential macro is inside that branch, so an empty source never enters it.
3. Emit a sequential Macro with executionmode 1, one source entry and fragment
   size 1. Declare a private Zone iterator inside this macro, using the observed
   type 8 / empty value / zone unit / array 0 record.
4. At the start of each iteration, copy that iterator into the semantic Var[Zone]
   with Set Variable, then emit the original body in order.

The semantic target is deliberately separate from the native iterator. Reassigning
it or passing it as a child-call output must not change the next native fragment.
The captured source likewise remains separate from the user's input variable.
Private names avoid user variables and loop/fragment counters; nested loops own
distinct storage. None of these variables enters either public semantic Program.

The condition and copy use already observed primitives; they are not invented
termination checks. The compiler reports unsupported_zone_index or
unsupported_zone_grouping for operations needing unverified bounds/divisibility
failure propagation. It does not use a dialog, a skipped statement or F43's
custom Error Handler as a substitute for stopping the program.

## Verification

Python, direct IR and JSON tests cover order, empty state, persistent targets,
source/target writes, child-call outputs, nested loops, grouping failures before
effects and step limits. Consumer checks cover specialization, configuration,
timers and list-output initialization. Static XML checks inspect capture,
macro-local declarations, parameter destinations, counter names and the outer
empty guard. Existing v4 JSON/UUID/ASFP baselines remain unchanged.

Executor acceptance, native Zone copy/enumeration and actual error propagation
remain pending. Record those results separately before widening the target.

## Version

Version: none for this evidence note; implementation belongs to stage 14.
