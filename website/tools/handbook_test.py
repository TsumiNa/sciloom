"""Keep complete handbook snippets executable and example pages tied to source."""

import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

from website.tools import tutorials

ROOT = Path(__file__).resolve().parents[2]

# Cumulative tutorial series; see website/docs/developer/documentation.md.
SERIES: dict[str, tutorials.Series] = {
    "user-guide/tutorial": tutorials.Series(
        pages=(
            "user-guide/tutorial/first-function",
            "user-guide/tutorial/inputs-and-units",
            "user-guide/tutorial/lists-and-loops",
            "user-guide/tutorial/agitator",
            "user-guide/tutorial/compile",
        ),
        complete="examples/stir_rack.py",
    ),
}


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
        "user-guide/troubleshooting",
        "developer/reference/ir",
        "developer/reference/pipeline",
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


@pytest.mark.parametrize(
    "page",
    ("developer/add-a-device", "developer/add-a-target", "developer/reject-a-program"),
)
def test_complete_tutorial_snippet(page, tmp_path):
    """Tutorials build up in steps, so their complete program is the last block."""
    markdown = (ROOT / f"website/docs/{page}.md").read_text()
    source = re.findall(r"```python\n(.*?)\n```", markdown, re.DOTALL)[-1]
    example = tmp_path / "tutorial_example.py"
    example.write_text(source)
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    subprocess.run([sys.executable, str(example)], cwd=tmp_path, env=env, check=True)


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
        ("examples/function-call", "function_call"),
        ("examples/agitation", "agitation"),
        ("examples/scale-values", "scale_values"),
        ("examples/non-zero-array-min", "non_zero_array_min"),
        ("examples/stir-rack", "stir_rack"),
        ("user-guide/tutorial/compile", "stir_rack"),
        ("examples/agitation-ir", "developer/agitation_ir"),
        ("examples/list-ir", "developer/list_ir"),
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
