# IR validation and JSON

The current interchange contract is **JSON v4**. Import these functions from `sciloom.core.ir`.

Thermal scalar vocabulary adds `temperature`, `temperature_difference` and
`temperature_rate` to existing Literal/Variable/ListType records. Canonical values
are K, K and K/s respectively. Existing kinds and bytes retain their meaning;
older readers may explicitly reject the new enum values. See the
[temperature example](../examples/temperature-values.md) for a complete document.

::: sciloom.core.ir.validate

::: sciloom.core.ir.to_dict

::: sciloom.core.ir.from_dict

::: sciloom.core.ir.to_json

::: sciloom.core.ir.from_json
