"""For developers: thermal Python fields, JSON v4 and persistent reference state.

Run: ``uv run python -m examples.developer.temperature_ir``
Expected terminal output:
    temperature_ir.json
    Target: 298.15 K; first change: 5.00 K; second change: 0.00 K

The complete JSON is the same-name companion. This is core/reference execution;
AutoSuite rejects thermal types until native encoding and range behavior are
verified. Canonical SI values never incorporate the observed vendor offset.
"""

from pathlib import Path

from examples.temperature_values import TemperatureValues
from sciloom import Temperature, TemperatureDifference, TemperatureRate, degC, degC_per_min, delta_degC, kelvin_per_s
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from .source_paths import repository_relative

if __name__ == "__main__":
    program = repository_relative(TemperatureValues().to_ir())
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(program), encoding="utf-8")
    restored = from_json(path.read_text(encoding="utf-8"))
    assert restored == program
    session = Interpreter(restored)
    inputs: dict[str, Temperature | TemperatureDifference | TemperatureRate] = {
        "initial": 20 * degC,
        "step": 5 * delta_degC,
        "ramp": 60 * degC_per_min,
    }
    first = session.run(inputs=inputs)
    second = session.run(inputs=inputs)
    target, change, repeated_change = first.outputs["target"], first.outputs["change"], second.outputs["change"]
    assert isinstance(target, Temperature) and target == 25 * degC
    assert isinstance(change, TemperatureDifference) and change == 5 * delta_degC
    assert isinstance(repeated_change, TemperatureDifference) and repeated_change == 0 * delta_degC
    assert first.outputs["rate"] == 1 * kelvin_per_s
    print(path.name)
    print(
        f"Target: {target.kelvin:.2f} K; first change: {change.kelvin:.2f} K; second change: {repeated_change.kelvin:.2f} K"
    )
