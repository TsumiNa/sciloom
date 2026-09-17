# Units

Import quantity types and units from `sciloom`. Values use cubic metres, seconds
and revolutions per second internally. Volume and duration can be signed;
rotational speed remains nonnegative. All numeric values must be finite.

Absolute temperature uses kelvin and the standard Celsius offset of 273.15.
`TemperatureDifference` is signed kelvin; `TemperatureRate` is signed kelvin
per second. Absolute temperature cannot be negative, added to another absolute
temperature, or scaled. These types support core/reference execution; AutoSuite
thermal encodings remain gated. See the [temperature example](../examples/temperature-values.md).

`FlowRate` stores signed finite cubic metres per second, and `Length` stores
signed finite metres. Use `mL_per_min`, `m3_per_s`, `mm` and `metre`; operation
and deployment contracts impose positive flow or permitted positions separately.
These values have source/IR/JSON/reference support. Native AutoSuite encoding
remains gated. See [transfer settings](../examples/transfer-settings.md).

::: sciloom.FlowRate

::: sciloom.Length

::: sciloom.mL_per_min

::: sciloom.m3_per_s

::: sciloom.mm

::: sciloom.metre

::: sciloom.units.FlowRateUnit

::: sciloom.units.LengthUnit

::: sciloom.Temperature

::: sciloom.TemperatureDifference

::: sciloom.TemperatureRate

::: sciloom.degC

::: sciloom.kelvin

::: sciloom.delta_degC

::: sciloom.delta_kelvin

::: sciloom.degC_per_min

::: sciloom.kelvin_per_s

::: sciloom.units.TemperatureUnit

::: sciloom.units.TemperatureDifferenceUnit

::: sciloom.units.TemperatureRateUnit

::: sciloom.Volume

::: sciloom.Duration

::: sciloom.uL

::: sciloom.mL

::: sciloom.L

::: sciloom.s

::: sciloom.minute

::: sciloom.hour

::: sciloom.units.VolumeUnit

::: sciloom.units.DurationUnit

::: sciloom.RotationalSpeed

::: sciloom.rpm

::: sciloom.rps

::: sciloom.units.SpeedUnit
