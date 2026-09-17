# Example walkthroughs

Every walkthrough includes the actual runnable source and its expected result.
Generated companions are included where the target can produce them; gated
examples show the current diagnostic instead. Use a source checkout to run the listed commands.
Downloads are learning references; generated JSON records source paths relative
to the repository root.

## For experiment authors

| Example | What it teaches |
|---|---|
| [Function calls](function-call.md) | Pass a value to a child Function and receive its result |
| [Agitation](agitation.md) | Save a speed, start or stop a shaker, and compile for AutoSuite |
| [Scale values](scale-values.md) | Copy a list and multiply each element by a factor |
| [Non Zero Array Min](non-zero-array-min.md) | Find the smallest value above a threshold in supplied numbers |
| [Stir a rack of samples](stir-rack.md) | Choose a speed from supplied volumes and count start requests |
| [Prepare labels](prepare-labels.md) | Trim supplied text, select a part and return independent labels |
| [Quantity conversion](quantity-conversion.md) | Calculate volumes and time differences with explicit units |
| [Numeric operations](numeric-operations.md) | Calculate whole portions and an absolute volume difference |
| [Record values](record-values.md) | Log supplied sample labels and typed volumes |
| [Confirm samples](confirm-samples.md) | Require OK before recording a ready sample |
| [Capture a barcode](capture-barcode.md) | Validate one well, capture text and save/log it only after acceptance; native compilation remains gated |
| [Timestamp a filename](timestamp-path.md) | Capture local wall time once and build a filename |
| [Timed agitation](timed-agitation.md) | Wait relative to a timer before explicitly stopping agitation |
| [Read a reagent table](read-reagent-table.md) | Select a heading and aligned typed columns; AutoSuite compilation remains gated |
| [Append a sample log](append-sample-log.md) | Append one text record; AutoSuite mode and encoding still need verification |
| [Resolve sample locations](resolve-locations.md) | Combine named Zones and count distinct wells |
| [Visit sample locations](visit-locations.md) | Visit one well at a time using a declared Zone loop variable |
| [Label selected wells](label-wells.md) | Write a sample identifier to selected wells and read it back |
| [Run a selected shaker](stir-selected-location.md) | Configure, select, start, wait and stop; native emission remains gated |
| [Label wells and append a log](label-sample-log.md) | Combine confirmation, time, ordered metadata changes and file writes |
| [Calculate a volume chunk](aspiration-chunk.md) | Calculate capacity, partial fills and a caller-supplied resume point |
| [Temperature values](temperature-values.md) | Distinguish absolute temperature, differences and rates |
| [Fixed heater intent](warm-sample.md) | Configure, explicitly start, wait a duration and stop |
| [Transfer settings](transfer-settings.md) | Calculate typed flow rates and lengths |
| [Single-well transfer](transfer-sample.md) | Capture one explicit source/destination pair and validate fixed capacity |
| [Operator and equipment workflows](expansion-workflows.md) | Compose barcode, heater, shaker and transfer operations with shared child configuration |

## For contributors

| Example | What it verifies |
|---|---|
| [Agitation IR](agitation-ir.md) | JSON persistence and configured/applied state snapshots |
| [List IR](list-ir.md) | Direct construction and value semantics |
| [Reference environment](reference-environment.md) | Shared event history and independent session state |
| [Typed log IR](logging-ir.md) | Capture a quantity in an immutable event after JSON restoration |
| [Confirmation IR](confirmation-ir.md) | Consume an explicit response after JSON restoration |
| [Wall-time IR](wall-time-ir.md) | Supply an aware clock and inspect an immutable read event |
| [Elapsed-time IR](timing-ir.md) | Advance a virtual clock without sleeping or changing wall time |
| [Typed CSV IR](csv-read-ir.md) | Restore a read from JSON and execute with explicit file bytes |
| [CSV append IR](csv-append-ir.md) | Append twice in memory and inspect captured records |
| [Zone IR](zone-ir.md) | Query an explicit immutable location directory after JSON restoration |
| [Zone traversal IR](zone-traversal-ir.md) | Index an ordered selection and visit complete groups after JSON restoration |
| [Physical device snapshots](device-locations-ir.md) | Select two controllers while retaining independent applied values and running states |
| [Well property IR](well-properties-ir.md) | Supply an explicit metadata store and inspect immutable read/write events |
| [Independent device](demo-device.md) | A new property, command and target outside core |
| [Explicit lifecycle effects](lifecycle-commands.md) | Typed apply/disable contracts with captured configuration |
| [Portable agitation](portable-agitation.md) | Device specialization and rebinding the same authored JSON |
| [Complete workflows from IR](runtime-workflows-ir.md) | Three independent builders, JSON restoration and explicit reference services |
| [Volume chunk after JSON](aspiration-chunk-ir.md) | Source-derived quantity arithmetic and repeated calls after restoration |
| [Expansion integration](expansion-workflows.md) | Direct-IR/source/JSON parity, mixed devices, native gates and review-export conditions |
