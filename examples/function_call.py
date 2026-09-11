"""For experiment authors: compose functions and export an ASFP package."""

from pathlib import Path

from sciloom.backends.autosuite import AutoSuiteTarget
from sciloom import Function, Input, Output, Real, runtime


class Identity(Function):
    x: Input[Real]
    y: Output[Real]

    @runtime
    def run(self):
        self.y = self.x


class Caller(Function):
    result: Real = 0.0

    def __init__(self, value: float = 2.5):
        self.value = value
        self.identity = Identity()

    @runtime
    def run(self):
        self.result = self.identity(x=self.value)


if __name__ == "__main__":
    result = Caller().compile(target=AutoSuiteTarget())
    path = result.write(Path("dist") / "function_call.asfp")
    print(path)
