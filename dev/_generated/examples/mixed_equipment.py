"""For experiment authors: label a sample, then run two shared equipment cycles.

Run: ``uv run python examples/mixed_equipment.py``
Output: ``Mixed equipment awaits verified AutoSuite profiles and native gates.``

Barcode acceptance precedes metadata, logging and all device actions. The parent
saves settings; one shared child explicitly starts, waits ten seconds, transfers,
stops and logs. A changed flow is applied by the second transfer. A fixed wait
does not establish temperature. Failure does not synthesize stops or rollback.
The developer mixed_equipment_ir example supplies explicit reference services.
"""

from sciloom import (
    Agitator,
    Function,
    Heater,
    Input,
    LiquidHandler,
    Output,
    Var,
    WellProperty,
    Zone,
    degC,
    degC_per_min,
    log,
    mL,
    mL_per_min,
    request_text,
    rpm,
    runtime,
    s,
    wait,
    zones,
)
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class EquipmentCycle(Function):
    """Use the parent's saved configuration through shared logical references."""

    heater: Heater
    shaker: Agitator
    liquid: LiquidHandler
    source: Input[Zone]
    destination: Input[Zone]

    @runtime
    def run(self) -> None:
        self.heater.start()
        self.shaker.start()
        wait(10 * s)
        self.liquid.transfer(self.source, self.destination, 0.25 * mL)
        self.shaker.stop()
        self.heater.stop()
        log("transfer complete", category="liquid", stream="experiment")


class MixedEquipment(Function):
    """Capture sample metadata before two explicitly controlled equipment cycles."""

    source: Input[Zone]
    destination: Input[Zone]
    barcode: Output[str]
    well_name: Var[str] = ""
    heater: Heater
    shaker: Agitator
    liquid: LiquidHandler

    def __init__(self) -> None:
        self.sample_id = WellProperty("sample_ID", str)
        self.cycle = EquipmentCycle()
        self.cycle.heater = self.heater
        self.cycle.shaker = self.shaker
        self.cycle.liquid = self.liquid

    @runtime
    def run(self) -> None:
        self.well_name = zones.well_name(self.destination)
        self.barcode = request_text("Barcode for " + self.well_name, timeout=30 * s)
        self.sample_id[self.destination] = self.barcode
        log(self.barcode, category="samples", stream="barcode")
        self.heater.temperature = 20 * degC
        self.heater.ramp_rate = 1 * degC_per_min
        self.shaker.speed = 300 * rpm
        self.liquid.aspirate_flow = 1 * mL_per_min
        self.liquid.dispense_flow = 2 * mL_per_min
        self.liquid.air_gap = 0.05 * mL
        self.cycle(source=self.source, destination=self.destination)
        self.liquid.aspirate_flow = 3 * mL_per_min
        self.cycle(source=self.source, destination=self.destination)


if __name__ == "__main__":
    try:
        MixedEquipment().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "missing_resource_binding" for d in error.diagnostics):
            raise
        print("Mixed equipment awaits verified AutoSuite profiles and native gates.")
    else:
        raise AssertionError("No native mixed-equipment profile has been validated.")
