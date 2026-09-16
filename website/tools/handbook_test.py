"""Keep complete handbook snippets executable and example pages tied to source."""

import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from textwrap import indent

import pytest

from examples.non_zero_array_min import NonZeroArrayMin
from examples.scale_values import ScaleValues
from sciloom.core.interpreter import Interpreter
from website.tools import tutorials

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "values,factor,expected",
    [([1.0, 2.0, 3.0], 2.5, (2.5, 5.0, 7.5)), ([], 2.5, ()), ([1.0, 2.0], 0.0, (0.0, 0.0))],
)
def test_scale_walkthrough_results(values, factor, expected):
    original = list(values)
    snapshot = Interpreter(ScaleValues().to_ir()).run(inputs={"values": values, "factor": factor})
    assert snapshot.outputs["result"] == expected
    assert values == original


@pytest.mark.parametrize(
    "values,expected",
    [([0.0, 4.0, 2.0, 0.0], 2.0), ([], 999999.0), ([0.0, 0.0], 999999.0), ([1e-8, 3.0], 3.0), ([1000000.0], 999999.0)],
)
def test_minimum_walkthrough_results(values, expected):
    snapshot = Interpreter(NonZeroArrayMin().to_ir()).run(inputs={"values": values})
    assert snapshot.outputs["minimum"] == expected


# Cumulative tutorial series; see website/docs/developer/documentation.md.
SERIES: dict[str, tutorials.Series] = {
    "developer/tutorial": tutorials.Series(
        pages=(
            "developer/tutorial/declare-a-family",
            "developer/tutorial/declare-profiles",
            "developer/tutorial/write-a-function",
            "developer/tutorial/write-a-target",
            "developer/tutorial/reject-a-program",
            "developer/tutorial/adapt-with-comptime",
            "developer/tutorial/execute-what-you-can",
            "developer/tutorial/complete-program",
        ),
    ),
}

USER_LESSONS = (
    ("first-function", "tutorial/start_shaker"),
    ("inputs-and-units", "tutorial/control_shaker"),
    ("agitator", "tutorial/choose_stirring_speed"),
    ("lists-and-loops", "tutorial/stir_sample_rack"),
    ("compile", "stir_rack"),
)


@pytest.mark.parametrize("page, source", USER_LESSONS)
def test_user_lesson_runs_independently(page, source, tmp_path):
    name = Path(source).name
    stdout = run_series_script(tmp_path / f"{name}.py", (ROOT / f"examples/{source}.py").read_text(), tmp_path)
    assert stdout == f"{name}.asfp\n"
    assert (tmp_path / f"{name}.asfp").read_bytes() == (ROOT / f"examples/{source}.asfp").read_bytes()
    markdown = (ROOT / f"website/docs/user-guide/tutorial/{page}.md").read_text()
    assert f"uv run python examples/{source}.py" in markdown
    assert f"```text\n{name}.asfp\n```" in markdown


def run_series_script(script, source, tmp_path):
    script.write_text(source)
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    completed = subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, env=env, check=True, capture_output=True, text=True
    )
    return completed.stdout


@pytest.mark.parametrize(
    "page",
    (
        "user-guide/advanced/composition",
        "user-guide/advanced/specialization",
        "user-guide/advanced/device-branches",
        "user-guide/advanced/autosuite",
        "developer/troubleshooting",
        "developer/reference/ir",
        "developer/advanced/specialization",
        "developer/advanced/json-interchange",
        "developer/reference/interpreter",
        "developer/reference/target-contract",
    ),
)
def test_complete_handbook_snippet(page, tmp_path):
    """A page's first program runs; a text fence right after it states its stdout."""
    markdown = (ROOT / f"website/docs/{page}.md").read_text()
    program = re.search(r"```python\n(.*?)\n```(?:\n```text\n(.*?)\n```)?", markdown, re.DOTALL)
    stdout = run_series_script(tmp_path / "handbook_example.py", program.group(1), tmp_path)
    if program.group(2) is not None:
        assert stdout.rstrip("\n") == program.group(2)


def test_troubleshooting_failure_examples(tmp_path):
    markdown = (ROOT / "website/docs/developer/troubleshooting.md").read_text()
    program = re.search(r"<!-- example: failures -->\n```python\n(.*?)\n```\n```text\n(.*?)\n```", markdown, re.DOTALL)
    assert program is not None
    assert run_series_script(tmp_path / "failures.py", program.group(1), tmp_path).rstrip("\n") == program.group(2)


@pytest.mark.parametrize(
    "name,fields,code,checks",
    (
        (
            "speed",
            "speed: Output[RotationalSpeed]",
            "type_mismatch",
            'assert session.run(inputs={}).outputs == {"speed": 600 * rpm}',
        ),
        (
            "loop",
            "values: Input[list[float]]\ntotal: Output[float]\nindex: Var[int] = 0",
            "python_subset",
            "for values, total in (([1.0, 2.0], 3.0), ([], 0.0), ([4.0], 4.0)):\n"
            '    assert session.run(inputs={"values": values}).outputs == {"total": total}',
        ),
        (
            "condition",
            "count: Input[int]\nselected: Output[bool]",
            "condition_type",
            "for count, selected in ((2, True), (0, False), (-1, False)):\n"
            '    assert session.run(inputs={"count": count}).outputs == {"selected": selected}',
        ),
        (
            "boolean",
            "a: Input[bool]\nb: Input[bool]\nboth: Output[bool]",
            "unsupported_short_circuit",
            "for a in (False, True):\n"
            "    for b in (False, True):\n"
            '        assert session.run(inputs={"a": a, "b": b}).outputs == {"both": a and b}',
        ),
        (
            "list-output",
            "values: Input[list[float]]\nresult: Output[list[float]]\nindex: Var[int] = 0",
            "list_output_initialization",
            "for values in ([1.0, 2.0], [], [4.0]):\n"
            '    assert session.run(inputs={"values": values}).outputs == {"result": tuple(x * 2 for x in values)}',
        ),
        (
            "configuration",
            "shaker: Agitator\nspeed: Input[RotationalSpeed]\nenabled: Input[bool]",
            "device_configuration",
            "for enabled in (False, True, False):\n"
            '    result = session.run(inputs={"speed": 300 * rpm, "enabled": enabled})\n'
            '    assert result.resources["resource:shaker"].enabled == enabled',
        ),
        (
            "timer",
            "timer: Timer\nenabled: Input[bool]",
            "timer_not_started",
            "for enabled, elapsed in ((True, 5), (False, 5), (True, 10)):\n"
            '    session.run(inputs={"enabled": enabled})\n'
            "    assert clock.monotonic() == elapsed",
        ),
    ),
)
def test_troubleshooting_corrections(name, fields, code, checks, tmp_path):
    """Compile the published failure and run its correction, including boundary inputs."""
    markdown = (ROOT / "website/docs/user-guide/troubleshooting.md").read_text()
    imports = (
        "from sciloom import Agitator, Function, Input, Output, RotationalSpeed, Timer, Var, rpm, runtime, s\n"
        "from sciloom.core.diagnostics import DiagnosticError\n"
        "from sciloom.core.interpreter import Interpreter, ReferenceEnvironment, VirtualClock\n"
        "from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget\n\n"
    )
    target = "AutoSuiteTarget()"
    if name == "configuration":
        target = (
            'AutoSuiteTarget(devices={"shaker": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")})'
        )
    for form in ("wrong", "fixed"):
        snippet = re.search(rf"<!-- correction: {name} {form} -->\n```python\n(.*?)\n```", markdown, re.DOTALL)
        assert snippet is not None
        source = imports + "class Example(Function):\n" + indent(fields, "    ")
        source += "\n\n    @runtime\n    def run(self) -> None:\n" + indent(snippet.group(1), "        ")
        source += f"\n\ntarget = {target}\n"
        if form == "wrong":
            source += (
                "try:\n    Example().compile(target=target)\n"
                "except DiagnosticError as error:\n    print(error.diagnostics[0].code)\n"
            )
            expected = code
        else:
            if name == "timer":
                source += "clock = VirtualClock()\n"
                source += "session = Interpreter(Example().compile(target=target).specialized_ir, environment=ReferenceEnvironment(clock=clock))\n"
            else:
                source += "session = Interpreter(Example().compile(target=target).specialized_ir)\n"
            source += checks + '\nprint("ok")\n'
            expected = "ok"
        assert run_series_script(tmp_path / f"{name}_{form}.py", source, tmp_path).strip() == expected


def test_troubleshooting_retains_diagnostic_catalogue():
    """Reorganizing help must not drop codes from the previous author catalogue."""
    markdown = (ROOT / "website/docs/user-guide/troubleshooting.md").read_text()
    entries = re.findall(r"^\| `([a-z_]+)` \|", markdown, re.MULTILINE)
    assert len(entries) >= 66
    codes = set(entries)
    assert codes >= {
        "unsupported_runtime_guard",
        "unsupported_text_length",
        "unsupported_text_literal",
        "call_binding",
        "class_schema",
        "condition_type",
        "device_capability",
        "device_condition",
        "device_configuration",
        "device_property",
        "device_property_read",
        "device_reference",
        "device_type",
        "host_value",
        "index_type",
        "list_element_type",
        "list_output_initialization",
        "list_type",
        "missing_resource_binding",
        "operation_binding",
        "operator_type",
        "python_subset",
        "quantity_literal",
        "recursive_call",
        "runtime_field",
        "runtime_field_read",
        "runtime_field_write",
        "runtime_method",
        "source_unavailable",
        "type_mismatch",
        "unknown_resource_binding",
        "unsupported_operation",
        "unsupported_short_circuit",
    }


@pytest.mark.parametrize(
    "name, index, block",
    [(name, index, block) for name, series in SERIES.items() for index, block in tutorials.checkpoints(ROOT, series)],
)
def test_tutorial_checkpoint(name, index, block, tmp_path):
    """A checkpoint's text is the stdout its page adds to the pages before it."""
    series = SERIES[name]
    script = tmp_path / Path(series.complete or "tutorial.py").name
    before = run_series_script(script, tutorials.program(ROOT, series, index - 1), tmp_path)
    after = run_series_script(script, tutorials.program(ROOT, series, index) + "\n\n" + block.code, tmp_path)
    assert after.startswith(before)
    assert after[len(before) :].rstrip("\n") == block.expected


@pytest.mark.parametrize("name", list(SERIES))
def test_tutorial_series_is_the_complete_program(name):
    series = SERIES[name]
    steps = tutorials.program(ROOT, series, len(series.pages) - 1)
    assert tutorials.same_program(steps, tutorials.complete_program(ROOT, series))


@pytest.fixture(scope="module")
def rendered():
    subprocess.run([sys.executable, str(ROOT / "website/tools/site.py"), "build", "--strict"], check=True)
    return ROOT / "website/.build/site"


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, value):
        self.parts.append(value)


@pytest.mark.parametrize(
    "page, source",
    (
        ("introduction/getting-started", "tutorial/start_shaker"),
        ("examples/function-call", "function_call"),
        ("examples/agitation", "agitation"),
        ("examples/scale-values", "scale_values"),
        ("examples/non-zero-array-min", "non_zero_array_min"),
        ("examples/stir-rack", "stir_rack"),
        *((f"user-guide/tutorial/{page}", source) for page, source in USER_LESSONS),
        ("examples/agitation-ir", "developer/agitation_ir"),
        ("examples/list-ir", "developer/list_ir"),
        ("examples/reference-environment", "developer/reference_environment"),
        ("examples/record-values", "record_values"),
        ("examples/logging-ir", "developer/logging_ir"),
        ("examples/demo-device", "developer/demo_device"),
        ("examples/portable-agitation", "developer/portable_agitation"),
    ),
)
def test_walkthrough_includes_actual_source(rendered, page, source):
    text = Text()
    text.feed((rendered / f"{page}/index.html").read_text())
    expected = (ROOT / f"examples/{source}.py").read_text()
    assert expected.strip() in "".join(text.parts)
    assert (rendered / f"_generated/examples/{source}.py").read_text() == expected
