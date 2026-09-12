"""For SciLoom developers: construct and execute JSON v3 list semantics directly.

Run from the repository root:
    uv run python -m examples.developer.list_ir

Expected output:
    list_ir.json
    (9.0, 2.0)
    [1.0, 2.0]

The output is an independent list value, exposed as a tuple in the immutable
snapshot. The caller's Python input remains unchanged. Full generated JSON is in
list_ir.json beside this source. This example uses reference execution and does
not compile AutoSuite instructions or send commands to hardware.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import (
    Assignment, FunctionIR, ListSet, ListType, Literal, Program, Reference,
    ScalarType, Variable, VariableRole, from_json, to_json,
)


def build_program() -> Program:
    numbers = ListType(element_type=ScalarType.REAL)
    function = FunctionIR(
        node_id="edit", name="EditCopy",
        variables=(
            Variable(node_id="values", owner_id="edit", name="values", role=VariableRole.INPUT, type=numbers),
            Variable(node_id="result", owner_id="edit", name="result", role=VariableRole.OUTPUT, type=numbers),
        ),
        body=(
            Assignment(node_id="copy", target=Reference(node_id="copy-out", symbol_id="result"), value=Reference(node_id="copy-in", symbol_id="values")),
            ListSet(node_id="set", target=Reference(node_id="set-out", symbol_id="result"), index=Literal(node_id="index", type=ScalarType.INTEGER, value=0), value=Literal(node_id="value", type=ScalarType.REAL, value=9.0)),
        ),
    )
    return Program(entry_function_id="edit", functions=(function,))


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    values = [1.0, 2.0]
    result = Interpreter(program).run(inputs={"values": values})
    assert result.outputs["result"] == (9.0, 2.0)
    assert values == [1.0, 2.0]
    print(path.name)
    print(result.outputs["result"])
    print(values)
