"""For experiment authors: distinguish absolute temperature from a change.

Run: ``uv run python examples/temperature_values.py``
Expected terminal output:
    Target: 298.15 K
    Change: 5.00 K
    Ramp: 1.00 K/s

The host calculation below exercises the same value rules as the Function.
For runtime fields and JSON/reference execution, run the developer companion
``uv run python -m examples.developer.temperature_ir``. Native thermal encoding
is gated; this example does not drive a heater or establish arrival at a setpoint.
"""

from sciloom import (
    Function,
    Input,
    Output,
    Temperature,
    TemperatureDifference,
    TemperatureRate,
    Var,
    degC,
    degC_per_min,
    delta_degC,
    runtime,
)


class TemperatureValues(Function):
    """Calculate a new target and retain it across calls.

    Attributes:
        initial: Supplied absolute temperature, not an instrument reading.
        step: Signed change to add.
        ramp: Supplied rate, without any device-specific range claim.
        target: Calculated absolute target.
        change: Change from the previously saved target.
        rate: Typed rate copied to the caller without applying it to a device.
        saved: Previous target, initialized to 20°C.
    """

    initial: Input[Temperature]
    step: Input[TemperatureDifference]
    ramp: Input[TemperatureRate]
    target: Output[Temperature]
    change: Output[TemperatureDifference]
    rate: Output[TemperatureRate]
    saved: Var[Temperature] = 20 * degC

    @runtime
    def run(self) -> None:
        self.target = self.initial + self.step
        self.change = self.target - self.saved
        self.saved = self.target
        self.rate = self.ramp


if __name__ == "__main__":
    initial = 20 * degC
    target = initial + 5 * delta_degC
    change = target - initial
    ramp = 60 * degC_per_min
    print(f"Target: {target.kelvin:.2f} K")
    print(f"Change: {change.kelvin:.2f} K")
    print(f"Ramp: {ramp.kelvin_per_second:.2f} K/s")
