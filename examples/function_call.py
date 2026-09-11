"""For experiment authors: compose functions and export an ASFP package.

Run from the repository root:
    uv run python examples/function_call.py

Expected terminal output:
    function_call.asfp

The package contains Caller and Identity. Caller passes x=2.5 to Identity and
binds its output y to the internal variable result. Identity assigns y=x.
Compilation writes these instructions; it does not execute them.

Full generated output: function_call.asfp, beside this source file.

Generated ASFP excerpts (parameter IDs and other fields omitted):

    Execute Function input binding:
        <item0>
          <!-- parameter ID omitted -->
          <name>x</name>
          <variablename />
          <variabletype>realnumber</variabletype>
          <isarray>0</isarray>
          <expression>2.5</expression>
        </item0>

    Execute Function output binding:
        <item0>
          <!-- parameter ID omitted -->
          <name>y</name>
          <variablename>result</variablename>
          <variabletype>realnumber</variabletype>
          <isarray>0</isarray>
          <expression />
        </item0>

    Identity's Set Variable task:
        <variablename>y</variablename>
        <expressiontext>x</expressiontext>
"""

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
    path = result.write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
