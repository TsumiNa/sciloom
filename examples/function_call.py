"""Compile Test12-style functions to ASFP; all outputs stay outside the corpus."""

from pathlib import Path

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
    result = Caller().compile()
    path = result.write(Path("dist") / "function_call.asfp")
    path.with_suffix(".ir.json").write_text(to_json(result.semantic_ir), encoding="utf-8")
    print(path)
