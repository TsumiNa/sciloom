"""Keep the logging example's reference behavior and ASFP companion aligned."""

from pathlib import Path

from sciloom import mL
from sciloom.core.interpreter import Interpreter, LogEvent
from sciloom_autosuite import AutoSuiteTarget
from .record_values import RecordValues


def test_record_values_example():
    example = RecordValues()
    result = Interpreter(example.to_ir()).run(inputs={"sample": "A", "amount": 1 * mL})
    assert all(isinstance(event, LogEvent) for event in result.events)
    assert [(e.category, e.stream, e.value) for e in result.events] == [
        ("recipe", "sample", "A"),
        ("A", "volume", 1 * mL),
    ]
    assert (
        example.compile(target=AutoSuiteTarget()).artifact.content
        == Path(__file__).with_name("record_values.asfp").read_bytes()
    )
