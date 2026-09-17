"""The committed review bundle is reproducible across checkout locations."""

from pathlib import Path

from sciloom.core.compiler import compile_ir
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteTarget, write_autosuite_review
from . import source_paths
from .deployment_review import Accumulator


def test_report_digest_survives_checkout_relocation(tmp_path, monkeypatch):
    program = Accumulator().to_ir()
    original = source_paths.repository_relative(program)
    relocated = from_json(to_json(program).replace(str(source_paths.REPOSITORY_ROOT), str(tmp_path)))
    monkeypatch.setattr(source_paths, "REPOSITORY_ROOT", tmp_path)
    rewritten = source_paths.repository_relative(relocated)
    assert rewritten == original
    target = AutoSuiteTarget()
    result = compile_ir(rewritten, target=target)
    path = tmp_path / "review.asfp"
    report = write_autosuite_review(result, target=target, path=path)
    companion = Path(__file__).with_name("deployment_review.deployment.json")
    assert report.to_json() == companion.read_text()
    assert path.read_bytes() == companion.with_name("deployment_review.asfp").read_bytes()
