"""Frontend layering: vocabulary above analysis, one recorded seam, lazy author API."""

import ast
import subprocess
import sys
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent
PACKAGES = ("flow", "dsl")

# What an author writes, evaluated while a class body runs.
VOCABULARY = frozenset({"flow.comptime", "flow.device_slots", "flow.fields", "flow.function"})
# What runs only inside Function.to_ir().
ANALYSIS = frozenset(
    {
        "dsl.context",
        "dsl.device_conditions",
        "dsl.device_operations",
        "dsl.driver",
        "dsl.expressions",
        "dsl.source",
        "dsl.statements",
    }
)

# The frontend's only back edge: the author entry reaches the analysis layer, which
# needs the Function class at runtime. Adding a second entry needs a contract change.
DEFERRED_IMPORTS = frozenset({("flow.function", "dsl.driver")})


def modules() -> dict[str, ast.Module]:
    """Parse every production module of both frontend packages."""
    found = {}
    for package in PACKAGES:
        for path in sorted((FRONTEND / package).glob("*.py")):
            if path.stem in {"__init__", "conftest"} or path.stem.endswith("_test"):
                continue
            found[f"{package}.{path.stem}"] = ast.parse(path.read_text(encoding="utf-8"))
    return found


def qualify(dotted: str) -> set[str]:
    """Name the frontend module a dotted path refers to, if it is one."""
    for package in PACKAGES:
        prefix = f"sciloom.{package}."
        if dotted.startswith(prefix):
            return {f"{package}.{dotted[len(prefix) :].split('.')[0]}"}
    return set()


def targets(node: ast.Import | ast.ImportFrom, package: str) -> set[str]:
    """Return the frontend modules that one import statement depends on."""
    if isinstance(node, ast.Import):
        return {name for alias in node.names for name in qualify(alias.name)}
    if node.level == 1:
        if node.module is None:
            return {f"{package}.{alias.name}" for alias in node.names}
        return {f"{package}.{node.module.split('.')[0]}"}
    if node.module is None:
        return set()
    if node.module in {f"sciloom.{name}" for name in PACKAGES}:
        owner = node.module.removeprefix("sciloom.")
        return {f"{owner}.{alias.name}" for alias in node.names}
    return qualify(node.module)


def imports(tree: ast.Module, package: str) -> tuple[set[str], set[str]]:
    """Split frontend imports into module-level and function-local ones."""
    local = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for inner in ast.walk(node)
        if isinstance(inner, ast.Import | ast.ImportFrom)
    }
    top_level: set[str] = set()
    deferred: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            (deferred if id(node) in local else top_level).update(targets(node, package))
    return top_level, deferred


def edges() -> dict[str, tuple[set[str], set[str]]]:
    return {name: imports(tree, name.split(".")[0]) for name, tree in modules().items()}


def test_the_scanner_covers_both_import_forms():
    tree = ast.parse("import sciloom.dsl.context\n\n\ndef lower():\n    from sciloom.flow import function\n")
    assert imports(tree, "dsl") == ({"dsl.context"}, {"flow.function"})


def test_every_production_module_is_classified():
    assert set(modules()) == VOCABULARY | ANALYSIS


def test_function_local_imports_are_the_recorded_seams():
    found = {(name, target) for name, (_, deferred) in edges().items() for target in deferred}
    assert found == set(DEFERRED_IMPORTS)


def test_vocabulary_never_imports_analysis_at_module_level():
    for name in sorted(VOCABULARY):
        assert not edges()[name][0] & ANALYSIS, name


def test_module_level_graph_is_acyclic():
    graph = {name: top for name, (top, _) in edges().items()}
    ordered: list[str] = []
    while len(ordered) < len(graph):
        ready = sorted(name for name, used in graph.items() if name not in ordered and used <= set(ordered))
        assert ready, f"cycle among {sorted(set(graph) - set(ordered))}"
        ordered.extend(ready)


def test_author_imports_do_not_load_source_analysis():
    script = """
import sys
import sciloom

assert sciloom.Function is not None
assert sciloom.Input is not None
assert sciloom.comptime is not None
loaded = {name for name in sys.modules if name.startswith("sciloom.dsl")}
assert not loaded, loaded
"""
    subprocess.run([sys.executable, "-c", script], check=True)
