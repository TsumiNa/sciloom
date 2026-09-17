# Deployment conditions and state-lifetime measurements

## Current boundary

AutoSuiteTarget now accepts read-only AutoSuiteDeployment facts. Known product
mismatch, known layout/APP provenance mismatch and reset-enabled APPs with
persistent requirements reject in target validation. Every internal Var and
configured logical device conservatively needs persistence. No liveness analysis,
global-variable promotion or automatic APP editing is performed.

Offline generation remains available. write_autosuite_review writes an ASFP and
a same-base deployment.json report with exact artifact and canonical selected
IR hashes. Unknown facts remain unknown; compatible means only these deployment
checks passed. Native state-lifetime acceptance is **pending** for both settings.
CompileResult.write remains an artifact-only method.

The primary config20260909_polymerization.app has root resetvariables=1.
The manual's application settings (§3.5.1, p46) and Macro variable discussion
(p118) describe re-entry reset. Editor screenshots 18/21 show the setting checked
and disabled. This is sufficient for a conservative incompatibility diagnostic,
not proof of the generated Macro's behavior at every native call boundary.
See the [evidence register](../../docs/refactor/autosuite-expansion/04-evidence.md).

## Generate measurements

From the repository root:

```console
uv run python -m autosuite.tools.probe_state_lifetime --output-dir /tmp/sciloom-state-probes
```

Use a fresh scratch directory outside corpus. The tool shares the existing
failure-probe checkout/version helper and probe_format=1 provenance conventions.
It emits four ASFP/semantic-JSON/deployment-report bundles plus a manifest. It
does not synthesize an APP, edit evidence, run Executor, or pass an unchecked flag
to the compiler. It intentionally compiles offline measurement candidates.

| Case | First call counter log | Second call, same reference session | Fresh reference session |
| --- | --- | --- | --- |
| entry | 1 | 2 | 1 |
| shared | 1, 2 | 3, 4 | 1, 2 |
| distinct | 1, 1 | 2, 2 | 1, 1 |
| loop | 1, 2, 3 | 4, 5, 6 | 1, 2, 3 |

Pair probes reuse one child or create two independent children. Loop explicitly
resets only its iteration counter, then invokes its accumulating child three
times. All counter logs use category sciloom.state_probe and stream counter.
Reference expectations are calculated after JSON restoration, with a fresh
session for the third run. Fresh reference initialization does not establish
what a native APP restart does to saved variables.

## Host procedure and receipts

1. Preserve the original corpus and the generated manifest. On the AutoSuite
   host, create separate scratch APPs through the Editor for reset=0 and reset=1.
   Record actual root settings, product/profile version and exact APP hashes.
   The disabled UI state in a screenshot is not permission to edit XML manually;
   if the setting cannot be changed through supported vendor operations, record
   that experiment as unavailable and seek the vendor's procedure.
2. Import each ASFP, record its original hash, save and re-export it, and hash the
   re-export. Capture warnings and any Editor changes. Record how the main task
   calls the named entry twice in sequence, without re-import/reset between calls.
   Caller wiring and any additional tasks are part of the receipt.
3. Run the exact deployment-host command following
   [Executor instructions](15_EXECUTOR_SIMULATION.md), including the actual APP
   path and `/r /sim 100 /s /c`. Retain command, exit status, ordered native logs,
   output values and source/generated/re-exported identities. Do not infer success
   from exit status alone. No physical action is needed by these counter probes.
4. Restart the application through the documented host lifecycle and call once
   again. Record whether the APP was saved, reloaded or a new Executor process was
   started; these operations may have different persistence behavior. Record
   observations rather than copying the fresh-reference expectation.
5. Repeat all four cases under both reset values, retaining separate receipts.
   Compare first/second/restart results and shared/independent ownership. An
   unavailable reset setting or ambiguous restart lifecycle leaves that row
   pending. A single passing accumulator does not verify all call boundaries.

No native receipt is supplied in this PR. State probes do not unlock any runtime
failure, CSV, dynamic location or other guarded operation. Evidence that native
persistence cannot match SciLoom's contract requires reassessment; do not change
Var lifetime or silently add global state to make an experiment pass.
