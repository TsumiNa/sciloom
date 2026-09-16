"""For experiment authors: build a CSV filename from one runtime clock read.

Run: ``uv run python examples/timestamp_path.py``
Terminal output: ``timestamp_path.asfp``

When called with directory="results" at local time 2026-09-16 14:05:06,
the generated function returns stamp="2026-09-16_140506" and
path="results/2026-09-16_140506.csv". It constructs text; it does not create
a directory or file. Repeated calls within one second may produce the same name.

Compilation writes the complete timestamp_path.asfp companion beside this code.
The clock is read when AutoSuite calls the function, not during compilation.
"""

from pathlib import Path

from sciloom import Function, Input, Output, now_text, runtime
from sciloom_autosuite import AutoSuiteTarget


class TimestampPath(Function):
    """Name a result file using the platform's local wall time.

    Attributes:
        directory: Directory text supplied by the runtime caller.
        stamp: Captured timestamp, also available to later steps.
        path: Directory and timestamp joined into a CSV path.
    """

    directory: Input[str]
    stamp: Output[str]
    path: Output[str]

    @runtime
    def run(self) -> None:
        self.stamp = now_text("%Y-%m-%d_%H%M%S")
        self.path = self.directory + "/" + self.stamp + ".csv"


if __name__ == "__main__":
    path = TimestampPath().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
