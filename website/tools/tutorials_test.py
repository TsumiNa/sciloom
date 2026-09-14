"""Marked fences across pages form one verifiable program."""

import pytest

from website.tools import tutorials

STEP = "<!-- tutorial: step -->\n```python\nx = 1\n```\n"
FRAGMENT = "```python\nignored = True\n```\n"
CHECKPOINT = "<!-- tutorial: checkpoint -->\n```python\nprint(x)\n```\n```text\n1\n```\n"
TEXT_ONLY = "<!-- tutorial: checkpoint -->\n```text\nhello\n```\n"


def test_blocks_keep_marked_fences_in_order_and_ignore_fragments():
    found = tutorials.blocks(f"# Page\n\n{FRAGMENT}\n{STEP}\nProse.\n\n{CHECKPOINT}\n{TEXT_ONLY}")
    assert [(block.kind, block.code, block.expected) for block in found] == [
        ("step", "x = 1", None),
        ("checkpoint", "print(x)", "1"),
        ("checkpoint", "", "hello"),
    ]


def test_malformed_markers_are_errors():
    with pytest.raises(ValueError, match="step needs a python fence"):
        tutorials.blocks("<!-- tutorial: step -->\n```text\nno code\n```\n")
    with pytest.raises(ValueError, match="step needs a python fence"):
        tutorials.blocks("<!-- tutorial: step -->\n\n```python\nnot adjacent = True\n```\n")
    with pytest.raises(ValueError, match="checkpoint needs a text fence"):
        tutorials.blocks("<!-- tutorial: checkpoint -->\n```python\nprint(1)\n```\n\n```text\n1\n```\n")
    with pytest.raises(ValueError, match="checkpoint needs a text fence"):
        tutorials.blocks("<!-- tutorial: checkpoint -->\n```python\nprint(1)\n```\n")


def write_series(root, pages):
    for slug, markdown in pages.items():
        path = root / "website/docs" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown)


def test_program_accumulates_steps_and_checkpoints_carry_their_page(tmp_path):
    write_series(
        tmp_path,
        {
            "guide/one": f"{STEP}{CHECKPOINT}",
            "guide/two": "<!-- tutorial: step -->\n```python\ny = x + 1\n```\n" + TEXT_ONLY,
        },
    )
    series = tutorials.Series(pages=("guide/one", "guide/two"))
    assert tutorials.program(tmp_path, series, 0) == "x = 1"
    assert tutorials.program(tmp_path, series, 1) == "x = 1\n\ny = x + 1"
    assert [(index, block.expected) for index, block in tutorials.checkpoints(tmp_path, series)] == [
        (0, "1"),
        (1, "hello"),
    ]


def test_complete_program_is_the_last_fence_or_the_named_file(tmp_path):
    write_series(tmp_path, {"guide/last": f"{STEP}\n```python\nx = 1\n\ny = 2\n```\n"})
    inline = tutorials.Series(pages=("guide/last",))
    assert tutorials.complete_program(tmp_path, inline) == "x = 1\n\ny = 2"
    (tmp_path / "program.py").write_text("x = 1\n")
    named = tutorials.Series(pages=("guide/last",), complete="program.py")
    assert tutorials.complete_program(tmp_path, named) == "x = 1\n"


def test_same_program_ignores_docstring_and_import_layout_but_not_statements():
    steps = 'from pathlib import Path\nclass A:\n    """Doc."""\n    x = 1\n\nfrom sciloom import Var, runtime\n'
    module = '"""Module docstring."""\n\nfrom pathlib import Path\n\nfrom sciloom import runtime, Var\n\n\nclass A:\n    """Doc."""\n\n    x = 1\n'
    assert tutorials.same_program(steps, module)
    assert not tutorials.same_program(steps, module.replace("x = 1", "x = 2"))
    assert not tutorials.same_program(steps, module.replace('"""Doc."""', '"""Other."""'))
    assert not tutorials.same_program(steps, module.replace("runtime, Var", "Var"))
    assert not tutorials.same_program("from .helpers import x\n", "from helpers import x\n")
