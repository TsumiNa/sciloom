"""For experiment authors: select an allowed shaker, run it for five seconds, stop.

Run: ``uv run python examples/stir_selected_location.py``
Expected output:
    Supply --app configuration.app to validate the candidate deployment.
    AutoSuite dynamic ASFP emission awaits verified runtime failure propagation.

With --app, this script reads that APP without modifying it, checks the example
23/22 profiles and confirms the current compilation diagnostic. Replace those
profiles with your actual deployment. No ASFP is written while that gate remains
open. Compilation never runs the shaker. Speeds and waits illustrate programming,
not an experimental recipe. developer/runtime_workflows_ir.py demonstrates the
same procedure with explicit reference services and no equipment.
"""

import argparse
from pathlib import Path

from sciloom import Agitator, Function, Input, RotationalSpeed, Zone, at, runtime, s, wait
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteAgitatorSelection, AutoSuiteIndividualShaker, AutoSuiteLayout, AutoSuiteTarget


class StirSelectedLocation(Function):
    """Run one physical controller selected through a Zone input.

    Attributes:
        shaker: Logical device with explicitly allowed physical candidates.
        location: Nonempty selection inside one candidate's allowed wells.
        speed: Configuration captured before selecting the location.
    """

    shaker: Agitator
    location: Input[Zone]
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        self.shaker.speed = self.speed
        with at(self.shaker, self.location):
            self.shaker.start()
            wait(5 * s)
            self.shaker.stop()


def deployment(path: Path) -> AutoSuiteTarget:
    """Read actual APP ownership for the example's allowed shaker profiles."""
    return AutoSuiteTarget(
        layout=AutoSuiteLayout.from_app(path),
        devices={
            "shaker": AutoSuiteAgitatorSelection(
                candidates=(
                    AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
                    AutoSuiteIndividualShaker(zone="Heater Shaker 22", device_id="22"),
                )
            )
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate explicit shaker candidates; dynamic ASFP is currently gated."
    )
    parser.add_argument("--app", type=Path, help="Existing AutoSuite application; read only")
    args = parser.parse_args()
    if args.app is None:
        print("Supply --app configuration.app to validate the candidate deployment.")
    else:
        try:
            StirSelectedLocation().compile(target=deployment(args.app))
        except CompilationError as error:
            if not error.diagnostics or any(d.code != "unsupported_device_location" for d in error.diagnostics):
                raise
        else:
            raise AssertionError("Update this example after verified dynamic ASFP support lands.")
    print("AutoSuite dynamic ASFP emission awaits verified runtime failure propagation.")
