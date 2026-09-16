# Zone values and queries

Experiment authors import `Zone` and `zones` from `sciloom`.
See the [location reference](../user-guide/reference/zones.md) for current limits.

::: sciloom.Zone
    options:
      members: [empty, well_ids]

::: sciloom.zones
    options:
      members: [find, combine, well_name]

## Reference directories

These immutable records belong to `sciloom.core.locations`. A directory is
external to Program/JSON and is supplied through `ReferenceEnvironment`.

::: sciloom.core.locations.Well

::: sciloom.core.locations.LocationDirectory
