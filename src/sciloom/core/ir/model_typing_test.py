"""Deleting a supported handler must fail type checking at the closed-union guard.

This mutation check exercises the production dispatchers in a disposable copy.
It does not maintain a second registry of nodes or execute modified code.
"""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("mutation_kind", ["missing_node", "missing_zone_node", "new_unary_operation"])
def test_missing_consumer_handlers_fail_exhaustiveness(tmp_path, mutation_kind):
    root = Path(__file__).resolve().parents[4]
    for package, source in (
        ("sciloom", root / "src/sciloom"),
        ("sciloom_autosuite", root / "packages/sciloom-autosuite/src/sciloom_autosuite"),
    ):
        shutil.copytree(
            source, tmp_path / package, ignore=shutil.ignore_patterns("*_test.py", "__pycache__", "fixtures")
        )

    # One removed, supported branch in each semantic consumer. The remaining
    # union must reach assert_never and identify the omitted type in the error.
    omissions = {
        "sciloom/core/ir/expressions.py": "ListLiteral",
        "sciloom/core/ir/validation.py": "ListSet",
        "sciloom/core/specialization.py": "While",
        "sciloom/core/configuration.py": "While",
        "sciloom/core/timing.py": "While",
        "sciloom_autosuite/timing.py": "While",
        "sciloom/core/interpreter/expressions.py": "ListLiteral",
        "sciloom/core/interpreter/runtime.py": "ListSet",
        "sciloom_autosuite/expressions.py": "ListLiteral",
        "sciloom_autosuite/tasks.py": "ListSet",
        "sciloom_autosuite/validation.py": "ListSet",
    }
    if mutation_kind == "missing_zone_node":
        omissions = {name: "ZoneGet" if name.endswith("/expressions.py") else "ForEachZone" for name in omissions}
    if mutation_kind == "new_unary_operation":
        model = tmp_path / "sciloom/core/ir/model.py"
        model.write_text(model.read_text().replace('    NOT = "not"', '    NOT = "not"\n    UNHANDLED = "unhandled"'))
        omissions = {
            name: "UnaryOp.UNHANDLED"
            for name in (
                "sciloom/core/ir/expressions.py",
                "sciloom/core/interpreter/expressions.py",
                "sciloom_autosuite/expressions.py",
            )
        }

    class RemoveHandler(ast.NodeTransformer):
        def __init__(self, kind):
            self.kind = kind
            self.removed = 0

        def visit_If(self, node):
            test = node.test
            if (
                isinstance(test, ast.Call)
                and isinstance(test.func, ast.Name)
                and test.func.id == "isinstance"
                and len(test.args) == 2
                and isinstance(test.args[1], ast.Tuple)
            ):
                kinds = test.args[1].elts
                retained = [item for item in kinds if not (isinstance(item, ast.Name) and item.id == self.kind)]
                if len(retained) != len(kinds):
                    self.removed += 1
                    test.args[1].elts = retained
            if (
                isinstance(test, ast.Call)
                and isinstance(test.func, ast.Name)
                and test.func.id == "isinstance"
                and len(test.args) == 2
                and isinstance(test.args[1], ast.Name)
                and test.args[1].id == self.kind
            ):
                self.removed += 1
                return node.orelse
            return self.generic_visit(node)

    paths = []
    for name, kind in omissions.items():
        path = tmp_path / name
        if mutation_kind in ("missing_node", "missing_zone_node"):
            mutation = RemoveHandler(kind)
            changed = mutation.visit(ast.parse(path.read_text()))
            assert mutation.removed >= 1, name
            path.write_text(ast.unparse(changed))
        paths.append(str(path))

    config = tmp_path / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {tmp_path}\ncheck_untyped_defs = True\nshow_error_codes = True\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(config),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--follow-imports=silent",
            "--no-site-packages",
            *paths,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    for name, kind in omissions.items():
        assert any(
            name in line.replace("\\", "/") and '"assert_never"' in line and kind in line and '"Never"' in line
            for line in result.stdout.splitlines()
        ), result.stdout + result.stderr
