"""Python, direct IR and its committed JSON append the same records."""

from pathlib import Path

from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from .append_sample_log import AppendSampleLog
from .developer.csv_append_ir import build_program


def test_source_ir_and_json_append_identically():
    direct = build_program()
    companion = Path(__file__).parent / "developer/csv_append_ir.json"
    assert companion.read_text(encoding="utf-8") == to_json(direct)
    for program in (AppendSampleLog().to_ir(), direct, from_json(companion.read_text())):
        files = MemoryFiles()
        environment = ReferenceEnvironment(files=files)
        session = Interpreter(program, environment=environment)
        for _ in range(2):
            session.run(inputs={"path": "samples.csv", "label": "sample,A"})
        assert files.snapshot()["samples.csv"] == b'"sample,A"\r\n"sample,A"\r\n'
        assert tuple(event.values for event in environment.events) == (("sample,A",), ("sample,A",))
