# Example walkthroughs

Every walkthrough includes the actual runnable source, its expected result and
same-name generated companions. Use a source checkout to run the listed commands.
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
| [Timestamp a filename](timestamp-path.md) | Capture local wall time once and build a filename |
| [Timed agitation](timed-agitation.md) | Wait relative to a timer before explicitly stopping agitation |
| [Read a reagent table](read-reagent-table.md) | Select a heading and aligned typed columns; AutoSuite compilation remains gated |
| [Append a sample log](append-sample-log.md) | Append one text record; AutoSuite mode and encoding still need verification |
| [Resolve sample locations](resolve-locations.md) | Combine named Zones and count distinct wells |
| [Visit sample locations](visit-locations.md) | Visit one well at a time using a declared Zone loop variable |
| [Label selected wells](label-wells.md) | Write a sample identifier to selected wells and read it back |

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
| [Well property IR](well-properties-ir.md) | Supply an explicit metadata store and inspect immutable read/write events |
| [Independent device](demo-device.md) | A new property, command and target outside core |
| [Portable agitation](portable-agitation.md) | Device specialization and rebinding the same authored JSON |
