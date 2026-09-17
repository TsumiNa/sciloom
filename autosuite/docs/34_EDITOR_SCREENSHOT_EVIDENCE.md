# Editor screenshot evidence, received September 18, 2026

## Provenance and limits

The supplied AutoSuite_截图转录.zip contains 33 screenshots, two secondary Markdown
descriptions and test.asfp. The descriptions are an index, not verified vendor
statements or instructions. Original archive SHA-256:
`5b578f51b313f169361fddbfc1e196df062d8e606bed2996fb7f58fe39c2e841`.
Included ASFP SHA-256:
`9bce834bdc9981488b7a1612dcc12a390af684825f4c17712d8698bf5122b06a`.
Raw files remain outside git and are not rewritten.

The main-window title names config20260917_FRP_API.app. That APP was **not supplied**;
the screenshots' product/profile version is unknown. They do not replace the
primary config20260909_polymerization.app or vendor re-exports in the evidence
hierarchy. Do not assume product 2.47.1.1 merely because it is our target profile.

test.asfp is an incomplete Editor draft: one function, nine top-level components,
235 typed elements and 20 type IDs. Visible errors include an unselected operation,
unresolved function, incomplete CSV destinations/expressions and invalid subtasks.
It establishes some task envelopes and labels, not successful execution.

## Observations

| Screenshot / matching ASFP | Established observation | Limit |
| --- | --- | --- |
| 15_export_csv_general.png / Export CSV | Comma, CRLF and Append selected; delimitermode, endlinecharacter and exportbehaviour are all 0 in XML | A sample-specific UI/wire association; no actual append, bytes, encoding or other version's enum proof |
| 16_export_csv_export_data.png / same component | Column 1, Time result type, s unit, empty expression; Export Result unspecified | Not a valid complete export; blank settings are not recommended defaults |
| 18_macro_scan_and_assign_barcode.png and 21_macro_wait_temp_heating_lhs.png | Reset option checked/disabled | Manual §3.5.1 p46 / Macro variables p118 and primary APP resetvariables=1 motivate conservative rejection; native lifecycle tests pending |
| 08_transfer_volumetrically_transfer_values.png / well addresses | UI well numbers are 1-based; XML addresses are 0-based; visible upper rows belong to a 48-row list | Well index, well identity and controller ID differ; no general transfer execution proof |
| 21_macro_wait_temp_heating_lhs.png and 22_heat_cool.png | Local variable 50°C differs from task 20°C; XML has 323.16 and 293.16 | Apparent 273.16 offset requires precise input/re-export measurements; core SI remains 273.15 |
| 30_stir.png / Stir | Zone Heater Shaker 24 maps to controller Shaker 21 in this draft | Region labels are not physical controller IDs or uniqueness keys |

CSV label evidence is stronger than inference from repeated F46 tasks, but weaker
than an executed re-exported probe. The draft still has exportfilepath='C:', empty
exportresultvar and an empty column expression. A clear label association does
not make the enclosing program valid.

## Exact image identities

Names are relative to the archive's images directory. SHA-256 identifies original
bytes, not regenerated thumbnails or Markdown transcriptions.

| Image | SHA-256 |
| --- | --- |
| 03_editor_main_window_test_function.png | b249347542c7766d6d7e5162cf96234ae1cb5c30fc2188aa21196095e774a4df |
| 08_transfer_volumetrically_transfer_values.png | 10c5b0a3a60dacbd6c4f7865a944cbd28a0502f80f837a28eca681f634f61dbf |
| 15_export_csv_general.png | 45b3d2d642f088be16f5cb0ee6c118e88b706aa4d4c89e3e2e10a078313b6c35 |
| 16_export_csv_export_data.png | 558a50b56c21c401ef777c79214e97c582da215c516d74aee1c357e52844edfe |
| 18_macro_scan_and_assign_barcode.png | 902be03f255aff3ad441b283718da33bdc4402765f59f886e0d3ae05b123a1d8 |
| 21_macro_wait_temp_heating_lhs.png | c7bc5c3d85273c28d4fe784d5d445b3a502a425bd4da95929a3f53aef3597f26 |
| 22_heat_cool.png | 3bf42acc5b6a282389e7778a5260b7accd9f2a63aeee75bd591a1f7b134a6013 |
| 30_stir.png | e48917ff1863001b32831a32eefc51938251f71dab21cab26c258a297861de5a |

Use existing [failure](24_RUNTIME_FAILURE_GATE.md), [CSV read](27_CSV_READ_MAPPING.md),
[CSV append](28_CSV_APPEND_MAPPING.md) and [state lifetime](33_DEPLOYMENT_STATE_LIFETIME.md)
procedures. Associate received files through [receipt checks](35_NATIVE_MEASUREMENT_RECEIPTS.md).
No screenshot or transcript changes a native compilation gate.
