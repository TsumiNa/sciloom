"""Cover the rewrite boundary the developer examples depend on."""

from dataclasses import replace
from pathlib import Path

from sciloom import Function, Output, runtime
from sciloom.core.ir import Program, SourceSpan, to_dict
from .source_paths import repository_relative

OUTSIDE = "/elsewhere/vendor/library.py"


class Probe(Function):
    """Produce nested source spans from this test file.

    Attributes:
        result: Single output assigned by the runtime method.
    """

    result: Output[int]

    @runtime
    def run(self) -> None:
        self.result = 1


def source_paths(program: Program) -> set[str]:
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            source = node.get("source")
            if isinstance(source, dict) and isinstance(source.get("path"), str):
                found.add(source["path"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(to_dict(program))
    return found


def without_paths(program: Program) -> object:
    def strip(node: object) -> object:
        if isinstance(node, dict):
            return {key: ("" if key == "path" else strip(value)) for key, value in node.items()}
        if isinstance(node, list):
            return [strip(item) for item in node]
        return node

    return strip(to_dict(program))


def test_nested_in_repository_paths_become_relative():
    program = Probe().to_ir()
    absolute = str(Path(__file__).resolve())
    assert source_paths(program) == {absolute}
    assert any("source" in node for node in to_dict(program)["functions"][0]["body"])

    rewritten = repository_relative(program)
    assert source_paths(rewritten) == {"examples/developer/source_paths_test.py"}


def test_paths_outside_the_repository_are_left_alone():
    program = Probe().to_ir()
    moved = replace(program, functions=(replace(program.functions[0], source=SourceSpan(path=OUTSIDE, line=1)),))

    rewritten = repository_relative(moved)

    assert OUTSIDE in source_paths(rewritten)
    assert "examples/developer/source_paths_test.py" in source_paths(rewritten)


def test_rewriting_changes_nothing_but_paths_and_is_idempotent():
    program = Probe().to_ir()
    rewritten = repository_relative(program)

    assert without_paths(rewritten) == without_paths(program)
    assert repository_relative(rewritten) == rewritten
