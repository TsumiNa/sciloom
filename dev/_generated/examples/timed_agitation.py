"""For experiment authors: wait relative to a timer while a shaker stays running.

Run: ``uv run python examples/timed_agitation.py``
Terminal output: ``timed_agitation.asfp``

The generated function saves 300 rpm, starts the shaker, then starts a timer.
It waits two seconds, waits until five seconds from that timer start, and stops
the shaker. Reference execution advances five seconds; actual platform timing
needs Executor validation. The values illustrate programming, not a process recipe.

Compilation writes the complete timed_agitation.asfp beside this source. It
does not operate equipment or wait on the computer running this script.
"""

from pathlib import Path

from sciloom import Agitator, Function, Timer, rpm, runtime, s, wait
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget


class TimedAgitation(Function):
    """Keep agitation enabled until the elapsed-time step completes.

    Attributes:
        shaker: Logical shaker used for this procedure.
        timer: Function-owned origin for elapsed waits.
    """

    shaker: Agitator
    timer: Timer

    @runtime
    def run(self) -> None:
        self.shaker.speed = 300 * rpm
        self.shaker.start()
        self.timer.start()
        wait(2 * s)
        self.timer.wait_until(5 * s)
        self.shaker.stop()


if __name__ == "__main__":
    target = AutoSuiteTarget(
        devices={
            "shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
        }
    )
    path = TimedAgitation().compile(target=target).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
