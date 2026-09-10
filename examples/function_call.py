"""Runnable Function-to-IR example based on the Test12 call-binding fixture."""

from sciloom import Function, Input, Output, Real, runtime
from sciloom.ir import to_json


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
    print(to_json(Caller().to_ir()), end="")
