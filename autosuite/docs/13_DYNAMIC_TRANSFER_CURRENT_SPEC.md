# Dynamic Transfer Volumectrically - current AutoSuite-side implementation

Canonical implementation: the function named `Dynamic Transfer Volumectrically` extracted from `config20260909_polymerization.app`. The standalone `DynamicTransferVolumectrically_2.asfp` is retained as a historical/reference snapshot; when details differ, the newest full application is the source of truth.

## Interface

Inputs observed in the current application:

```text
bool      use_ch1
volume[]  array_vol
zone      dest_zone
volume    airgap_vol
volume    safe_vol
zone      source_zone
volume    extra_vol
bool      use_ch2
bool      use_ch3
integer   max_chunk_size
bool      use_ch4
text      source_zone_txt
```

No output parameter is exposed; execution status is carried through the project's global error-latch convention.

## Preconditions enforced by the function

1. `ZoneSize(dest_zone) == ArraySize(array_vol)`.
2. At least one syringe channel is enabled.
3. `max_chunk_size >= 1`.

Failures call `Throw Error` and latch the application error state.

## Stable index/residual state

The core state is `current_idx` plus `current_residual_vol`. This is important because a single requested well volume may exceed the usable syringe capacity and therefore be split without losing the original destination index.

The outer loop continues while no error is latched and the destination array has not been exhausted.

At each outer iteration the current group boundary is recomputed as:

```text
max_idx = floor(current_idx / max_chunk_size) * max_chunk_size
          + max_chunk_size - 1
```

This prevents a packed transfer from crossing the current bounded destination group. The caller currently selects `max_chunk_size=8` for small-syringe mode and `16` for large-syringe mode.

## Destination-zone construction and valve handling

For the current bounded group the function builds `dest_selected_zone` by repeatedly calling `Get Well Zone With Index` and concatenating single-well zones. It then calls `Set ISynth Drawer Valve` for that selected range before liquid handling.

Valve behavior should be treated as part of the current implementation contract rather than inferred from the human-readable Macro Task label: inspect the actual XML/function calls if changing modes.

## Per-channel packing

For every enabled channel that still has work in the current group:

1. save channel start index and residual volume;
2. query `Syringe Capasity`;
3. call `Get Aspirate Chunk`;
4. verify progress (same index + same residual within epsilon is an error);
5. if aspiration volume is nonzero, call `Aspirate From Source` with volume assigned to the corresponding channel.

After aspiration planning, each nonzero channel is dispatched through `Dispense Chunk` using its saved start/end indices and boundary residuals.

## `Get Aspirate Chunk`

Observed interface:

Inputs include start residual, full volume array, start index, syringe volume, max index, air-gap volume, safe volume and extra volume. Outputs include next index, end-dispense volume, next residual, total aspiration volume and end index.

The implementation computes usable capacity from syringe capacity minus margin volumes, packs requested destination amounts up to the capacity/group boundary, and handles an over-capacity destination by carrying residual volume to the next aspiration. The aspirated amount includes the configured extra volume.

## Why this function is a separate layer

It converts a logical request of the form "transfer this volume array to this destination zone" into a bounded series of hardware-executable aspiration/dispense chunks. CSV loading is upstream; 4NH and valve operations are downstream. Keeping this boundary separate is what allowed later valve-group limits and channel policies to be added without rewriting the reagent-table parser.

For exact structure, inspect `autosuite/corpus/extracted/latest_app/functions/30_Dynamic Transfer Volumectrically.asfp`. Use `autosuite/tools/inspect_structure.py` for a structural outline. The former summarized text views have been removed.
