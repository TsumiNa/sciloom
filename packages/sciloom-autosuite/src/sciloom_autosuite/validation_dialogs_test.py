"""Result and termination evidence is required even for static dialog inputs."""

import pytest

from sciloom import Function, Input, Output, Var, ask_yes_no, request_text, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import from_json, to_json
from sciloom.core.ir.traversal import iter_nodes
from .target import AutoSuiteTarget


class TextDialog(Function):
    value: Output[str]

    @runtime
    def run(self) -> None:
        self.value = request_text("Barcode")


class ChoiceDialog(Function):
    value: Output[bool]

    @runtime
    def run(self) -> None:
        self.value = ask_yes_no("Use sample?")


class ComposedDialog(Function):
    enabled: Input[bool]
    count: Var[int] = 0
    value: Var[str] = ""

    def __init__(self):
        self.child = TextDialog()

    @runtime
    def run(self) -> None:
        while self.count < 2:
            if self.enabled:
                self.value = self.child()
            self.count += 1


@pytest.mark.parametrize("model", [TextDialog, ChoiceDialog, ComposedDialog])
def test_native_dialog_gate_covers_json_composition_and_direct_emission(model):
    authored = model().to_ir()
    canonical = to_json(authored)
    target = AutoSuiteTarget()
    for program in (authored, from_json(canonical)):
        paths = {node.node_id: path for node, path in iter_nodes(program)}
        with pytest.raises(CompilationError) as error:
            compile_ir(program, target=target)
        diagnostics = [d for d in error.value.diagnostics if d.code == "unsupported_dialog_result"]
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.path == paths[diagnostic.node_id]
        assert diagnostic.source.path == __file__
        with pytest.raises(CompilationError, match="unsupported_dialog_result"):
            target.emit(program)
    assert to_json(authored) == canonical
