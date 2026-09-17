# Runtime failure propagation gate

**Executor status: pending.** The current checkout is macOS and has no
AutoSuiteExecutor.exe. This stage supplies generated probes, reference results
and a compiler restriction; it records no vendor execution or re-export result.
No manifest or user option enables an unverified failure mechanism.

## Candidate and evidence boundary

The existing numeric-list backend captures an index, changes a negative index
to `ArraySize(array)`, and reads the selected element before continuing. Manual
2.47.1.1 section 3.8.5, printed pp. 113–116, documents zero-based arrays and an
error beyond the upper bound. Section 3.9.4, pp. 136–137, describes an Error
Function followed by application termination. Neither passage alone proves
that the generated read triggers that fatal path across all callers and loops.

The array declarations, read expressions, Set Variable tasks and Macro/function
envelopes have the evidence recorded in [array mapping](17_ARRAY_MAPPING.md).
The combined failure mechanism is a candidate, not an original vendor-exported
failure probe. F32/F47's application error latch and dialog conventions are not
substitutes for fatal propagation. A successful XML parse, reference execution,
log message or skipped branch does not establish termination.

## Generate the probe packages

From a clean checkout of the source commit being evaluated:

```console
uv run python autosuite/tools/probe_runtime_failure.py --output-dir /tmp/sciloom-failure-probes
```

```text
Generated 9 probe pairs; Executor status: pending.
```

The destination must be new and outside `autosuite/corpus/`, including through
symlinks. Existing directories are refused. The tool writes nine ASFP/JSON pairs
and `manifest.json`; no input, corpus file or APP is modified. All packages use
only local numeric values and log markers, with no device operations.

Each scope has a one-element integer array and three variants: `control` reads
index 0, `out_of_range` reads index 1, and `negative` reads index -1. The latter
exercises the generated conversion to an upper-bound read. The manifest records
the actual reference result, expected ordered markers, node/source diagnostic,
artifact hashes, source commit/dirty flag, package versions and target identity.
Its `executor_status` is always `pending`, even when all reference tests pass.
Do not use a dirty-tree manifest as evidence for a clean source commit.
Versions are read from the source pyproject files, not installed distribution
metadata. The generator refuses mismatched versions or loaded authoring/target
implementations from another checkout before writing anything. Use
`uv sync --locked` in this checkout if the environment points elsewhere.

| Scope | Successful control markers | Expected prefix before candidate failure |
| --- | --- | --- |
| entry | `entry.before`, `entry.after` | `entry.before` |
| child | `caller.before`, `entry.before`, `entry.after`, `caller.after` | `caller.before`, `entry.before` |
| loop | `loop.before`, `loop.after`, `loop.before`, `loop.after`, `loop.finished` | one `loop.before` |

The reference failures report `index_bounds` at the selected list expression.
Earlier log events remain; no later marker or next iteration executes. Reference
execution cannot establish how AutoSuite classifies the same read.

## Host procedure and acceptance

Use one separate, disposable, known-good application per package. The three
variants reuse function names and must not be mixed into one application.
Configure logging so `sciloom.failure_probe/markers` is observable. Call the
manifest's entry function, then add a distinguishable `host.after` log task in
the application's caller. These functions have no inputs. Do not add an error
latch or recovery handler to imitate termination; record the application's
actual error-function configuration with the result.

Load/re-export in the Editor, retaining the original generated artifact and its
hash. Run the prepared application with the documented simulation command:

```bat
AutoSuiteExecutor.exe probe.app /r /sim 100 /s /c
```

The APP is prepared on the host; this tooling does not compile or modify one.
Use [the Executor reference](15_EXECUTOR_SIMULATION.md) for option semantics.

For each scope, first run its control. It must produce exactly the successful
marker sequence above, then `host.after`, with no error. This confirms that the
application actually invokes the function and that marker logging is observable.
An absent marker without this control is inconclusive.

Then run both failing variants in fresh applications. Require the expected
prefix, an actual native bounds error at the candidate read, and stopped
application execution. No remaining function marker, next loop iteration or
`host.after` may execute. An unrelated import error, manual stop, timeout, dialog
left open or missing logging configuration is not a passing failure result.
Inspect the completed run's log/task trace; exit code alone is insufficient.

Keep the source/target/AutoSuite versions, generated and re-exported ASFP hashes,
APP hash and error-function configuration, command, native error/exit information
and ordered marker trace. Record each case separately; passing the entry case
does not establish propagation through a child or loop. Repeatability and any
additional target versions require their own results. Store received evidence
through the team's human-managed corpus process, never by rewriting originals.

Use [receipt checks](35_NATIVE_MEASUREMENT_RECEIPTS.md) to associate exact
source/artifact hashes and all controls with received host traces. Successful
completeness remains pending_review and does not establish fatal propagation.

## Compiler gate and compatibility

Until those results establish a usable fatal mechanism, new target operations
that require it raise `unsupported_runtime_guard`. This includes dynamic text
split selectors, new text/volume/duration-list bounds checks, quantity division
with an unproved divisor, and speed scaling with an unproved sign/divisor.
Putting them in child calls, loops, logs, notifications or restored JSON does
not bypass validation. Diagnostics carry the full Program path, node ID and
source location, including the owning `functions[n]` prefix.

Previously accepted numeric-list programs remain accepted, as required by the
v4 compatibility contract; that is not a claim that their hardware failure
semantics are now proven. New guarded capabilities remain closed. Future work
must add a tested target implementation from reviewed Executor evidence rather
than flip a runtime option or treat this probe's manifest as authorization.

| XML / re-export | Manual semantics | Reference execution | Executor |
| --- | --- | --- | --- |
| Candidate emission inspected/tested; host re-export pending | Upper-bound errors and application error stopping documented separately | Nine control/failure cases, JSON restoration, earlier-event retention and exact failure sources tested | Unavailable here; entry, child, loop and outer caller propagation all pending |
