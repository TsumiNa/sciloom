"""The author's text example has reproducible output and reference results."""

from pathlib import Path

from examples.prepare_labels import PrepareLabels
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteTarget


def test_prepare_labels():
    function = PrepareLabels()
    result = Interpreter(function.to_ir()).run(inputs={"name": " Sample A,extra "})
    assert result.outputs == {"label": "Sample A_processed", "labels": ("Sample A_processed", "ready")}
    assert (
        function.compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("prepare_labels.asfp").read_bytes()
    )
