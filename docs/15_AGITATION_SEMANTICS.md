# Agitation: a domain operation retained in IR

This example probes architecture with a real operation supported by the production
AutoSuite corpus. It does not attempt a complete agitation or device model.

## Intent and resources

The Python frontend accepts a host component `Agitator("reaction_mixer")`, composed
before compilation. Calls to its `set_speed(speed)` and `stop()` methods inside
runtime source lower to explicit SetAgitation and StopAgitation nodes. Calling
these methods as host Python raises an error; they never contact a device.

Program.resources declares AgitatorResource records with a semantic node ID and
a logical_id. Equal logical IDs denote the same resource across composed functions;
unused host components are not added. Operations reference semantic IDs. A target
binds logical IDs to hardware separately; IR contains no Zone, device ID or typeid.

SetAgitation enables agitation and commands the supplied speed. StopAgitation
disables agitation, retaining the last known commanded speed in reference state.
A zero speed does not implicitly mean stop. No operation claims that the physical
speed has been reached or that the contents have mixed. Sharing this command
interface does not establish equivalence between different mixing mechanisms.

## Rotational-speed values

```python
from sciloom import Input, RotationalSpeed, rpm, rps

assert 600 * rpm == 10 * rps
# A Function declaration:
# speed: Input[RotationalSpeed]
```

RotationalSpeed is a finite nonnegative quantity. IR ScalarType.ROTATIONAL_SPEED
literals store revolutions per second; JSON uses type rotational_speed. Unitless
Real/Integer values cannot be implicitly assigned or passed as speeds.
Public interpreter inputs/outputs use RotationalSpeed objects. Internal state
snapshots retain canonical IR numeric values.

The initial frontend supports numeric host literals/configuration multiplied by
an imported rpm/rps constant, preconstructed host quantities, typed runtime
references, assignments and function parameter binding. It resolves only known
SpeedUnit values from module names, not arbitrary module globals or Python calls.
General dimensional arithmetic and runtime scalar-to-quantity conversion are
outside this slice. Scalar and quantity values cannot be mixed by arithmetic.

## Reference execution

AgitationState records enabled and an optional known speed, initially false/None
in a fresh reference session. This is a reference-model initial state, not a
measurement of connected hardware. AgitationEvent records the originating node,
resource and resulting commanded state, in execution order. Events are per run;
resource state persists in the session. Result snapshots are detached and immutable.

Python, hand-authored IR and JSON versions of a conditional configure-agitation
program produce matching start/stop state and events. A backend is not involved
in these tests. Raw numeric inputs, missing resources and inconsistent logical IDs
are explicit errors.

## AutoSuite deployment

The AutoSuite adapter binds logical resources explicitly to existing fixed zones
on individual shakers:

```python
from sciloom.backends.autosuite import AutoSuiteTarget, IndividualShakerBinding

target = AutoSuiteTarget(agitators=(
    IndividualShakerBinding(
        logical_id="reaction_mixer", zone="Heater Shaker 23", device_id="23",
    ),
))
result = function.compile(target=target)
```

This configuration belongs to the target, not Program. The device ID is the
shaker address, not the vessel/rack address in the Zone. Missing or unknown
bindings fail compilation; duplicate logical bindings, zones and physical aliases fail
configuration. The adapter supports the observed individual-shaker profile only,
not arbitrary agitation devices or dynamic Zone parameters.

Run `uv run python examples/agitation.py` for conditional start/stop reference
execution and generated `dist/agitation.asfp` / `dist/agitation.ir.json`.
Runtime inputs remain parameters in the ASFP; the interpreter inputs do not
specialize or run the exported file. The target accepts typed speeds in input/
output bindings, local declarations and expressions.

Stop serialization uses a documented inactive editor speed from the corpus;
it does not add a speed command or attempt to recover previous state.
See [mapping evidence](../autosuite/docs/16_AGITATION_MAPPING.md). Physical limits,
zone/device compatibility in a different application and Executor acceptance
still require deployment validation.

## Production evidence

The adapter is grounded in the retained latest APP's Sample and Run GPC
function (two SATaskSetAgitation nodes and an angularspeed input parameter).
Manual section 3.6.19 establishes set speed and on/off semantics; device speed
ranges depend on the selected device. This reference slice extracts the operation,
not the full GPC workflow or its physical sampling behavior.
