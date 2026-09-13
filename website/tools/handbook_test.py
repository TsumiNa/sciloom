"""Keep complete handbook snippets executable and example pages tied to source."""

import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "page",
    (
        "user-guide/values",
        "user-guide/compilation",
        "developer/ir",
        "developer/compiler",
        "developer/interpreter",
        "developer/contributions",
    ),
)
def test_complete_handbook_snippet(page, tmp_path):
    markdown = (ROOT / f"website/docs/{page}.md").read_text()
    source = re.findall(r"```python\n(.*?)\n```", markdown, re.DOTALL)[0]
    example = tmp_path / "handbook_example.py"
    example.write_text(source)
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    subprocess.run([sys.executable, str(example)], cwd=tmp_path, env=env, check=True)


@pytest.mark.parametrize("page", ("developer/add-a-device", "developer/add-a-target"))
def test_complete_tutorial_snippet(page, tmp_path):
    """Tutorials build up in steps, so their complete program is the last block."""
    markdown = (ROOT / f"website/docs/{page}.md").read_text()
    source = re.findall(r"```python\n(.*?)\n```", markdown, re.DOTALL)[-1]
    example = tmp_path / "tutorial_example.py"
    example.write_text(source)
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    subprocess.run([sys.executable, str(example)], cwd=tmp_path, env=env, check=True)


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
    "slug, source",
    (
        ("function-call", "function_call"),
        ("agitation", "agitation"),
        ("scale-values", "scale_values"),
        ("non-zero-array-min", "non_zero_array_min"),
        ("agitation-ir", "developer/agitation_ir"),
        ("list-ir", "developer/list_ir"),
        ("demo-device", "developer/demo_device"),
        ("portable-agitation", "developer/portable_agitation"),
    ),
)
def test_walkthrough_includes_actual_source(rendered, slug, source):
    text = Text()
    text.feed((rendered / f"examples/{slug}/index.html").read_text())
    expected = (ROOT / f"examples/{source}.py").read_text()
    assert expected.strip() in "".join(text.parts)
    assert (rendered / f"_generated/examples/{source}.py").read_text() == expected
