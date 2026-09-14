"""Cumulative tutorial series: marked fences across pages form one program.

A series is an ordered list of pages. Each page marks the fences that belong to
the series with an HTML comment on the preceding line: a ``step`` fence is
appended to the program, and a ``checkpoint`` runs the program built so far
(plus its own optional code) and states the stdout that run adds. Fences without
a marker are illustration and are never executed.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

MARK = re.compile(r"<!-- tutorial: (step|checkpoint) -->")
PYTHON = re.compile(r"\s*```python\n(.*?)\n```", re.DOTALL)
TEXT = re.compile(r"\s*```text\n(.*?)\n```", re.DOTALL)
ANY_PYTHON = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


@dataclass(frozen=True)
class Block:
    """One marked fence of a tutorial page.

    Attributes:
        kind: ``"step"`` or ``"checkpoint"``.
        code: Python source; empty for a text-only checkpoint.
        expected: Stdout a checkpoint adds, without the trailing newline; None for a step.
    """

    kind: str
    code: str
    expected: str | None


@dataclass(frozen=True)
class Series:
    """An ordered tutorial whose steps build one program.

    Attributes:
        pages: Page slugs under ``website/docs`` in reading order.
        complete: Repository-relative path of the complete program, or None when
            the last ``python`` fence of the last page is that program.
    """

    pages: tuple[str, ...]
    complete: str | None = None


def blocks(markdown: str) -> list[Block]:
    """Return the marked fences of one page in order.

    Raises:
        ValueError: A step has no python fence, or a checkpoint has no text fence.
    """
    found = []
    for mark in MARK.finditer(markdown):
        kind, position = mark.group(1), mark.end()
        code = PYTHON.match(markdown, position)
        if code is not None:
            position = code.end()
        if kind == "step":
            if code is None:
                raise ValueError("A tutorial step needs a python fence.")
            found.append(Block("step", code.group(1), None))
            continue
        expected = TEXT.match(markdown, position)
        if expected is None:
            raise ValueError("A tutorial checkpoint needs a text fence with its expected output.")
        found.append(Block("checkpoint", code.group(1) if code else "", expected.group(1)))
    return found


def _page(root: Path, slug: str) -> str:
    return (root / f"website/docs/{slug}.md").read_text()


def program(root: Path, series: Series, upto: int) -> str:
    """Return the step fences of ``pages[: upto + 1]`` joined into one program."""
    steps = []
    for slug in series.pages[: upto + 1]:
        steps.extend(block.code for block in blocks(_page(root, slug)) if block.kind == "step")
    return "\n\n".join(steps)


def checkpoints(root: Path, series: Series) -> list[tuple[int, Block]]:
    """Return every checkpoint with the index of the page it belongs to."""
    return [
        (index, block)
        for index, slug in enumerate(series.pages)
        for block in blocks(_page(root, slug))
        if block.kind == "checkpoint"
    ]


def complete_program(root: Path, series: Series) -> str:
    """Return the complete program the series must build."""
    if series.complete is None:
        return ANY_PYTHON.findall(_page(root, series.pages[-1]))[-1]
    return (root / series.complete).read_text()


def _imports(node: ast.Import | ast.ImportFrom) -> set[tuple[str | None, str, str | None]]:
    module = None if isinstance(node, ast.Import) else node.module
    return {(module, alias.name, alias.asname) for alias in node.names}


def _shape(source: str) -> tuple[frozenset[tuple[str | None, str, str | None]], list[str]]:
    body = ast.parse(source).body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        if isinstance(body[0].value.value, str):
            body = body[1:]
    imports: set[tuple[str | None, str, str | None]] = set()
    rest = []
    for node in body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            imports |= _imports(node)
        else:
            rest.append(ast.dump(node))
    return frozenset(imports), rest


def same_program(left: str, right: str) -> bool:
    """Compare two programs structurally.

    A leading module docstring is ignored, imported names are compared as a set,
    and the remaining top-level statements are compared in order.
    """
    return _shape(left) == _shape(right)
