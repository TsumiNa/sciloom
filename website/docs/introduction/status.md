# Current capabilities

With Python 3.12–3.14, you can write a procedure in a `.py` file and generate an
AutoSuite function package (`.asfp`). The current author API lets you:

- Declare inputs, outputs and working values, including typed lists.
- Process text and calculate volumes, time intervals and rotational speeds with explicit units.
- Calculate values, use `if` and `while`, and call reusable child Functions.
- Calculate magnitudes and round down; nearest-integer rounding of floats is available in reference execution, pending AutoSuite equivalence checks.
- Save shaker settings and explicitly start or stop agitation.
- Share a logical device between steps and bind it to an AutoSuite shaker.
- Choose device-specific branches when compiling for a target.
- Record supplied values and request an explicit OK acknowledgement before continuing.
- Capture wall time as text for filenames or records, using an explicit clock in reference execution.
- Wait for a duration or a Function-owned timer threshold while keeping device state unchanged.

The runtime method accepts a [restricted Python subset](../user-guide/reference/runtime-language.md).
Constructors and the surrounding script remain ordinary Python.

Typed [CSV reads and row appends](../user-guide/reference/csv.md) are also available in source,
JSON and reference execution. AutoSuite CSV compilation is explicitly unavailable
until its parsing, conversion, append mode, encoding and failure behavior can
meet the same contract.

## Runtime additions at a glance

All twelve additions below have typed IR, JSON v4 and reference execution.
The right column describes what the AutoSuite compiler currently accepts, not
what has passed Executor simulation. Follow the linked examples for complete
code, results and specific restrictions.

| Capability | AutoSuite compilation today |
|---|---|
| [Text and text lists](../examples/prepare-labels.md) | Declarations, copying, concatenation, comparison and trim; length only for literal BMP text, split with literal nonempty delimiter and nonnegative index; new text-list bounds guards remain gated |
| [Volume and Duration](../examples/quantity-conversion.md) | SI declarations and unit-aware arithmetic; new guarded quantity-list access is rejected |
| [Zone values and selection](../user-guide/reference/device-locations.md) | Named lookup, size and union; deployment ancestry checks work. Dynamic device scopes, well-name queries and nonempty Zone literals are rejected |
| [Zone indexing and traversal](../examples/visit-locations.md) | One-well sequential traversal; indexing and larger fragments await reliable runtime checks |
| [CSV reads](../examples/read-reagent-table.md) | Rejected pending literal conversion, defaults, result and failure equivalence |
| [CSV append](../examples/append-sample-log.md) | Rejected pending append mode, encoding and failure evidence |
| [Well text properties](../examples/label-wells.md) | Same-value writes; defaulted reads only with local proof of one well. Strict reads remain gated |
| [Waits and timers](../examples/timed-agitation.md) | Bounded literal durations and supported lexical timer scopes; dynamic durations and broader scope patterns are rejected |
| [Typed logs](../examples/record-values.md) | Captured scalar and quantity values |
| [OK confirmation](../examples/confirm-samples.md) | Text dialog with explicit OK continuation |
| [Numeric operations](../examples/numeric-operations.md) | `abs`, `floor`, integer `round`; floating `round` is rejected pending tie/range evidence |
| [Wall-time text](../examples/timestamp-path.md) | Selected constant formatting directives, evaluated once per call |

The [combined workflows](../examples/runtime-workflows-ir.md) exercise table
reading, a selected shaker and per-well logging with explicit reference services.
They do not produce native ASFP while the relevant target gates remain open.
Existing fixed-shaker and scalar tutorial programs continue to compile.

Contributors can define devices and targets. The developer examples include a
demonstration target, JSON v4 interchange and a reference interpreter for checking
calculations and state changes. That interpreter does not simulate laboratory hardware.

A visual editor, server, public Application/global API, measured property reads,
and notebook or interactive source support are not yet available.

## What compilation establishes

`AutoSuiteDeployment.from_app` now reads APP product/reset settings and exact-byte
provenance without modifying the file. Layouts read from APP also retain this
source hash. Deployment facts and report records are available, but integration
of reset-setting rejection into `AutoSuiteTarget` is not yet implemented.

Compilation checks the source, value types, declared device bindings and required
configuration before generating XML. It does not connect to the instrument or
prove that the procedure will run correctly on your deployment.

Generated packages still need AutoSuite Executor validation and equipment
acceptance. Array bounds checks, device mappings and fault/recovery behaviour
require platform verification; SciLoom's reference execution cannot establish
the instrument's numerical or physical behaviour.

The generated OK dialog is available for inspection and simulation; platform
execution remains unverified. Before equipment use, check on the AutoSuite host
that it blocks later steps until OK and resumes exactly once. The
[confirmation example](../examples/confirm-samples.md) describes that acceptance
gate. Supplying a response to the reference interpreter does not pass it.
