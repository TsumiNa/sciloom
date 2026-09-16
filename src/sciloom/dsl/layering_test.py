"""Frontend layering: vocabulary above analysis, one recorded seam, lazy author API."""

import ast
import subprocess
import sys
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent
PACKAGES = ("flow", "dsl")

# What an author writes, evaluated while a class body runs.
VOCABULARY = frozenset(
    {
        "flow.comptime",
        "flow.csv",
        "flow.device_slots",
        "flow.fields",
        "flow.function",
        "flow.text",
        "flow.zones",
        "flow.logging",
        "flow.messages",
        "flow.locations",
        "flow.properties",
        "flow.timing",
        "flow.timing_schema",
    }
)
# What runs only inside Function.to_ir().
ANALYSIS = frozenset(
    {
        "dsl.context",
        "dsl.csv_append",
        "dsl.csv_read",
        "dsl.device_conditions",
        "dsl.device_locations",
        "dsl.device_operations",
        "dsl.driver",
        "dsl.expressions",
        "dsl.source",
        "dsl.statements",
        "dsl.timing",
        "dsl.zone_iteration",
        "dsl.well_properties",
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


def package_imports(tree: ast.Module) -> set[str]:
    """Frontend packages imported whole, which would hide a module edge."""
    whole = {f"sciloom.{name}" for name in PACKAGES}
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name.removeprefix("sciloom.") for alias in node.names if alias.name in whole}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "sciloom":
            found |= {alias.name for alias in node.names if alias.name in PACKAGES}
    return found


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
    assert package_imports(ast.parse("import sciloom.dsl\nfrom sciloom import flow\n")) == {"dsl", "flow"}
    assert package_imports(tree) == set()


def test_lowering_state_is_always_the_first_parameter_named_context():
    for name, tree in modules().items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            positional = node.args.posonlyargs + node.args.args
            declared = positional + node.args.kwonlyargs + [node.args.vararg, node.args.kwarg]
            carriers = [
                argument.arg
                for argument in declared
                if argument is not None
                and isinstance(argument.annotation, ast.Name)
                and argument.annotation.id == "LoweringContext"
            ]
            if not carriers:
                continue
            assert carriers == ["context"], f"{name}.{node.name}"
            assert positional and positional[0].arg == "context", f"{name}.{node.name}"


def test_every_deferred_import_says_which_cycle_it_breaks():
    for package in PACKAGES:
        for path in sorted((FRONTEND / package).glob("*.py")):
            if path.stem.endswith("_test"):
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            tree = ast.parse("\n".join(lines))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                for inner in ast.walk(node):
                    if not isinstance(inner, ast.Import | ast.ImportFrom):
                        continue
                    above = [line.strip() for line in lines[: inner.lineno - 1] if line.strip()]
                    assert above and above[-1].startswith("#"), f"{path.name}:{inner.lineno}"


def test_no_module_imports_a_frontend_package_as_a_whole():
    for name, tree in modules().items():
        assert not package_imports(tree), name


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
assert sciloom.text is not None
loaded = {name for name in sys.modules if name.startswith("sciloom.dsl")}
assert not loaded, loaded
"""
    subprocess.run([sys.executable, "-c", script], check=True)
