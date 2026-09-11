# Agitation mapping evidence

This record supports the first SciLoom agitation adapter for AutoSuite 2.47.1.1.
It describes observed serialization and the limits of the selected profile.
Raw reference files are unchanged.

## Sources and provenance

| Evidence | What it establishes |
|---|---|
| Latest APP: `app/config20260909_polymerization.app` | Production context, current configuration and physical-variable storage |
| Extracted `extracted/latest_app/functions/24_Sample and Run GPC.asfp` | Current Stir task envelope and angularspeed parameter |
| `asfp/functionsPackage_3.asfp`, zone `1st_vial` | Fixed zone addressing on individual shaker 24 and 600 rpm numeric payload |
| `schema/type_templates/53_Chemspeed.SATaskSetAgitation.1_representative.xml` | Representative production start task |
| Manual section 3.6.19, pages 73–74 | Enable/disable and speed semantics, zone requirements, device-dependent speed range |

Paths in this table are relative to `autosuite/`.
The extracted function belongs to the latest APP, with function ID
`{DE6D061F-54C0-46C9-920E-17C2CBB56BA4}`.
It stops agitation before sampling and later restarts it. The conditional example
selects the same two operations; it does not reconstruct the whole GPC workflow.

The production stop ID is `{9AA7F57D-D1F0-4266-A086-D34F7541EB7B}`;
start ID is `{EA0D86C8-FC2A-49DA-9AA8-C1A44A6B7F3B}`.
The latter is also the representative template. The speed parameter
`shaker_speed`, ID `{4F3A4D0D-EE09-494B-ADE8-24035ACBBB83}`, has
`variabletype=angularspeed`. The production zone is the runtime parameter
`reactor_zone`; its task payload leaves progid and deviceid empty.

## Selected fixed-zone profile

The initial adapter binds one logical agitation controller to one existing fixed
zone on one individual shaker. It uses the production task envelope and the
concrete addressing variant established by the standalone export:

| Field | Meaning in this profile |
|---|---|
| typeid | `Chemspeed.SATaskSetAgitation.1` |
| zone | Bound application zone name |
| taskdatas/count | 1, uniform speed |
| taskdata0/progid | `Chemspeed.SADeviceIndividualShaker.1` |
| taskdata0/deviceid | Explicit bound shaker address |
| taskdata0/wellid | -1 |
| taskdata0/speed | Canonical speed expression when enabled |
| switchon | 1 for set speed, 0 for stop |
| speedunit | rpm, display metadata |
| autofillspeed | 1 |
| stirrertype | 0, observed profile value |

The shaker address is not the vessel or rack address stored in a Zone's well.
In the latest APP, zone `Heater Shaker 23` references well 27 of
`SADeviceISynthBlock2.1` device `1.1`. That block is nested under individual
shaker `23`. This is the runnable example's deployment binding; a regression
test checks the configuration relationship.

The backend requires explicit bindings and rejects missing/unknown logical IDs,
duplicate logical IDs and aliasing of distinct resources onto one shaker or zone.
It does not load the reference corpus during compilation. The caller must supply
a zone and shaker that exist together in the deployment application. Automatic
configuration discovery, other agitation mechanisms, multi-device zones and
runtime Zone parameters are not implemented by this adapter.

## Units and inactive speed

The latest APP's global `shaker_speed` stores numeric type 5, value 10,
siunit `1/s` and display unit `rpm`. The standalone 600 rpm task likewise stores
speed `10`. SciLoom therefore uses revolutions per second, with no 2π conversion;
the vendor type name angularspeed alone must not imply radians per second.
Function inputs/outputs use angularspeed; internal physical variables use storage
type 5, siunit 1/s and display unit rpm.

The production stop contains speed `1.66666666667`, an inactive 100 rpm editor
setting. Other exports retain different inactive values, including prior symbolic
speeds. The initial adapter uses this observed 100 rpm wire default only when
switchon=0. It does not issue a 100 rpm command, read a speed input, or introduce
hidden state to recover the previous speed. Reference execution retains its last
known commanded setpoint; that is not a claim about AutoSuite editor metadata.

The manual associates setting speed with the enabled state. Acceptance of this
generated disabled payload must still be confirmed through Executor. Device
speed bounds and physical speed attainment are outside static XML evidence.

## Comparison and remaining verification

The production comparison preserves all task fields and their order. It
normalizes task/component context, UUID spellings and timestamps, and explicitly
substitutes the fixed zone and individual-shaker address for the production
runtime Zone parameter. A second comparison uses the complete fixed-zone task
without address substitutions. Typed parameters, canonical units, call-binding
IDs and nesting inside conditional branches are checked separately.

These checks establish structural consistency, not AutoSuite import or execution
acceptance. No vendor XSD or Executor is available in this environment.
The complete observed .1 identifiers remain fixed; their formal suffix meaning
is still the [open vendor question](05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md#typeid-suffix-provisional-assumption-and-open-question).
