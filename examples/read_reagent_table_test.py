"""Author/IR/JSON examples agree on aligned IDs and explicitly scaled volumes."""

from pathlib import Path

from sciloom import mL
from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from .developer.csv_read_ir import build_program
from .read_reagent_table import ReadReagentTable


def test_recipe_source_and_direct_json_example():
    data = Path(__file__).with_name("read_reagent_table.csv").read_bytes()
    for program in (ReadReagentTable().to_ir(), from_json(to_json(ReadReagentTable().to_ir()))):
        result = Interpreter(program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data}))).run(
            inputs={"path": "recipe.csv", "reagent_index": 0}
        )
        assert result.outputs == {"reagent_name": "reagent_A", "ids": ("E01", "E02"), "volumes": (1.5 * mL, 0 * mL)}
    direct = build_program()
    companion = Path(__file__).parent / "developer/csv_read_ir.json"
    assert companion.read_text(encoding="utf-8") == to_json(direct)
    result = Interpreter(
        from_json(companion.read_text()), environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data}))
    ).run()
    assert result.outputs["ids"] == ("E01", "E02")
    assert result.outputs["volumes"] == (1.5 * mL, 0 * mL)
