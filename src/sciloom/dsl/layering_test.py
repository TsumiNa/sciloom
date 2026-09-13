"""Frontend layering: recorded seams only, no back edges, analysis stays unloaded."""

import ast
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
PREFIX = "sciloom.dsl"

# What an author writes, evaluated while a class body runs.
DECLARATIONS = frozenset({"comptime", "device_schema", "model", "schema"})
# What runs only inside Function.to_ir().
ANALYSIS = frozenset(
    {"context", "device_conditions", "device_operations", "expressions", "lowering", "source", "statements"}
)

# Every cycle the frontend still breaks with a function-local import. Removing an
# entry requires the matching source change; adding one requires a contract change.
DEFERRED_IMPORTS = frozenset(
    {
        ("device_conditions", "statements"),
        ("device_schema", "model"),
        ("expressions", "device_operations"),
        ("model", "lowering"),
    }
)


def modules() -> dict[str, ast.Module]:
    """Parse every production module of the frontend package."""
    return {
        path.stem: ast.parse(path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE.glob("*.py"))
        if path.stem not in {"__init__", "conftest"} and not path.stem.endswith("_test")
    }


def siblings(node: ast.ImportFrom) -> set[str]:
    """Return the sibling modules of this package that one statement imports."""
    if node.level == 1:
        if node.module is None:
            return {alias.name for alias in node.names}
        return {node.module.split(".")[0]}
    if node.module == PREFIX:
        return {alias.name for alias in node.names}
    if node.module is not None and node.module.startswith(f"{PREFIX}."):
        return {node.module[len(PREFIX) + 1 :].split(".")[0]}
    return set()


def imports(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Split sibling imports into module-level and function-local ones."""
    local = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for inner in ast.walk(node)
        if isinstance(inner, ast.ImportFrom)
    }
    top_level: set[str] = set()
    deferred: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            (deferred if id(node) in local else top_level).update(siblings(node))
    return top_level, deferred


def test_every_production_module_is_classified():
    assert set(modules()) == DECLARATIONS | ANALYSIS


def test_function_local_imports_are_the_recorded_seams():
    found = {(name, target) for name, tree in modules().items() for target in imports(tree)[1]}
    assert found == set(DEFERRED_IMPORTS)


def test_declarations_never_import_analysis_at_module_level():
    for name in sorted(DECLARATIONS):
        assert not imports(modules()[name])[0] & ANALYSIS, name


def test_module_level_graph_is_acyclic():
    graph = {name: imports(tree)[0] for name, tree in modules().items()}
    ordered: list[str] = []
    while len(ordered) < len(graph):
        ready = sorted(name for name, targets in graph.items() if name not in ordered and targets <= set(ordered))
        assert ready, f"cycle among {sorted(set(graph) - set(ordered))}"
        ordered.extend(ready)


def test_author_imports_do_not_load_source_analysis():
    analysis = ", ".join(repr(f"{PREFIX}.{name}") for name in sorted(ANALYSIS))
    script = f"""
import sys
import sciloom

assert sciloom.Function is not None
assert sciloom.Input is not None
assert sciloom.comptime is not None
loaded = set(sys.modules) & {{{analysis}}}
assert not loaded, loaded
"""
    subprocess.run([sys.executable, "-c", script], check=True)
