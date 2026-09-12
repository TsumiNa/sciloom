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

from sciloom.contrib.autosuite import AutoSuiteTarget
from sciloom import Function, Input, Output, Var, runtime


class Identity(Function):
    """Copy one numeric input to its output.

    Attributes:
        x: Value supplied by the caller.
        y: Copied value returned to the caller.
    """

    x: Input[float]
    y: Output[float]

    @runtime
    def run(self) -> None:
        self.y = self.x


class Caller(Function):
    """Specialize and call Identity with a host-configured value.

    Attributes:
        result: Persistent runtime state receiving Identity's output.
    """

    result: Var[float] = 0.0

    def __init__(self, value: float = 2.5) -> None:
        """Configure the call.

        Args:
            value: Host value embedded in the compiled call.
        """
        self.value = value
        self.identity = Identity()

    @runtime
    def run(self) -> None:
        self.result = self.identity(x=self.value)


if __name__ == "__main__":
    result = Caller().compile(target=AutoSuiteTarget())
    path = result.write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
