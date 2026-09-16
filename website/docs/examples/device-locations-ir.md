# Select physical shakers through IR

One logical mixer can use either of two controllers. This example starts A at
300 rpm, leaves it running, then starts B at 600 rpm and stops B. The logical
configuration holds 600 rpm afterward; A still has its separately applied value.

Run `uv run python -m examples.developer.device_locations_ir` from the checkout.
The terminal shows both physical states. The program is written as JSON v4 and
restored before execution. Its directory and candidate bindings are explicit
reference facts, supplied after restoration, so they can be replaced without
rewriting the JSON. No hardware is contacted.

```python
--8<-- "examples/developer/device_locations_ir.py"
```

`DeviceAt` captures and validates the location before entering the body. Its
exit releases that selection context, including after an error, but performs no
device operation. `physical_devices` is the map to inspect when more than one
controller may remain enabled. Old result snapshots cannot change after another
session call.

AutoSuite validates candidate profiles against APP well ancestry, but rejects
dynamic compilation until reliable native failure propagation is verified.
See [device locations](../user-guide/reference/device-locations.md) for the
author syntax and deployment boundary.

[Download Python](../_generated/examples/developer/device_locations_ir.py) ·
[Download JSON](../_generated/examples/developer/device_locations_ir.json)
