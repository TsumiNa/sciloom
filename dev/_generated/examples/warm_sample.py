"""For experiment authors: configure a heater, wait a fixed time, then stop.

Run: ``uv run python examples/warm_sample.py``
Output: ``AutoSuite heater profile awaits native validation.``

Both settings are explicit. Assignments save configuration; start applies it.
Ten seconds is a fixed wait, not evidence that the target temperature was reached.
The developer warm_sample_ir example supplies fixed reference bindings and a
virtual clock. No AutoSuite thermal profile is available in this stage.
"""

from sciloom import Function, Heater, degC, degC_per_min, runtime, s, wait
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class WarmSample(Function):
    """Demonstrate staged settings and explicit thermal lifecycle.

    Attributes:
        heater: Logical fixed heater, independently bound by a target.
    """

    heater: Heater

    @runtime
    def run(self) -> None:
        self.heater.temperature = 20 * degC
        self.heater.ramp_rate = 1 * degC_per_min
        self.heater.start()
        wait(10 * s)
        self.heater.stop()


if __name__ == "__main__":
    try:
        WarmSample().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "missing_resource_binding" for d in error.diagnostics):
            raise
        print("AutoSuite heater profile awaits native validation.")
    else:
        raise AssertionError("No native heater profile has been validated.")
