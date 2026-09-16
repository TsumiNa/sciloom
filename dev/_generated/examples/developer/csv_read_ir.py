"""For developers: typed CSV IR, JSON restoration and explicit in-memory files.

Run: ``uv run python -m examples.developer.csv_read_ir``
Expected terminal output:
    csv_read_ir.json
    IDs: ('E01', 'E02')
    Volumes (mL): (1.5, 0.0)
    Status: DEFAULT_USED

The complete JSON v4 artifact is csv_read_ir.json beside this source. The file
service receives fixed bytes explicitly; execution never reads the host disk.
The author example ../read_reagent_table.py also reads the reagent heading.
This is reference execution, not AutoSuite simulation or hardware validation.
"""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import (
    CsvColumn,
    CsvErrorPolicy,
    CsvReadMode,
    FunctionIR,
    ListType,
    Literal,
    Program,
    ReadCsv,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from sciloom.core.ir.csv import DEFAULT_USED
from sciloom.units import Volume, mL


def build_program() -> Program:
    """Read text IDs and millilitre cells into independent, aligned lists."""
    return Program(
        entry_function_id="read",
        functions=(
            FunctionIR(
                node_id="read",
                name="ReadVolumes",
                variables=(
                    Variable(
                        node_id="status",
                        name="status",
                        owner_id="read",
                        role=VariableRole.OUTPUT,
                        type=ScalarType.INTEGER,
                    ),
                    Variable(
                        node_id="ids",
                        name="ids",
                        owner_id="read",
                        role=VariableRole.OUTPUT,
                        type=ListType(element_type=ScalarType.TEXT),
                    ),
                    Variable(
                        node_id="volumes",
                        name="volumes",
                        owner_id="read",
                        role=VariableRole.OUTPUT,
                        type=ListType(element_type=ScalarType.VOLUME),
                    ),
                ),
                body=(
                    ReadCsv(
                        node_id="csv",
                        mode=CsvReadMode.COLUMNS,
                        error_policy=CsvErrorPolicy.STATUS,
                        path=Literal(node_id="path", type=ScalarType.TEXT, value="recipe.csv"),
                        header=True,
                        columns=(
                            CsvColumn(
                                index=Literal(node_id="id-index", type=ScalarType.INTEGER, value=0),
                                type=ScalarType.TEXT,
                            ),
                            CsvColumn(
                                index=Literal(node_id="volume-index", type=ScalarType.INTEGER, value=1),
                                type=ScalarType.VOLUME,
                                unit=Literal(node_id="unit", type=ScalarType.VOLUME, value=1e-6),
                                default=Literal(node_id="default", type=ScalarType.VOLUME, value=0),
                            ),
                        ),
                        targets=(
                            Reference(node_id="out-status", symbol_id="status"),
                            Reference(node_id="out-ids", symbol_id="ids"),
                            Reference(node_id="out-volumes", symbol_id="volumes"),
                        ),
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
    environment = ReferenceEnvironment(files=MemoryFiles({"recipe.csv": b"id,volume\nE01,1.5\nE02,\n"}))
    result = Interpreter(program, environment=environment).run()
    assert result.outputs["status"] == DEFAULT_USED
    print(path.name)
    print("IDs:", result.outputs["ids"])
    volumes = result.outputs["volumes"]
    assert isinstance(volumes, tuple)
    millilitres = []
    for value in volumes:
        assert isinstance(value, Volume)
        millilitres.append(value / mL)
    print("Volumes (mL):", tuple(millilitres))
    print("Status: DEFAULT_USED")
