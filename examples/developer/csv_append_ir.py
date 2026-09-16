"""For developers: append through explicit files and inspect captured events.

Run: ``uv run python -m examples.developer.csv_append_ir``
Expected terminal output:
    csv_append_ir.json
    File bytes: b'"sample,A"\\r\\n"sample,A"\\r\\n'
    Append events: 2

csv_append_ir.json is the complete companion JSON v4 program. MemoryFiles begins
empty; two calls append two independent records. Only the JSON companion is
written to the host. The CSV bytes printed above stay in memory. This is reference
execution, not an AutoSuite or instrument result.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import (
    AppendCsv,
    FunctionIR,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)


def build_program() -> Program:
    """Construct a row append from two caller-supplied text inputs."""
    return Program(
        entry_function_id="append",
        functions=(
            FunctionIR(
                node_id="append",
                name="AppendSampleLog",
                variables=tuple(
                    Variable(node_id=name, owner_id="append", name=name, type=ScalarType.TEXT, role=VariableRole.INPUT)
                    for name in ("path", "label")
                ),
                body=(
                    AppendCsv(
                        node_id="write",
                        path=Reference(node_id="path-read", symbol_id="path"),
                        values=(Reference(node_id="label-read", symbol_id="label"),),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(build_program()), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    assert program == build_program()
    files = MemoryFiles()
    environment = ReferenceEnvironment(files=files)
    session = Interpreter(program, environment=environment)
    session.run(inputs={"path": "samples.csv", "label": "sample,A"})
    session.run(inputs={"path": "samples.csv", "label": "sample,A"})
    print(path.name)
    print("File bytes:", files.snapshot()["samples.csv"])
    print("Append events:", len(environment.events))
