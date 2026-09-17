"""Review export associates settings with checked selected semantics and exact bytes."""

import hashlib
import json
from dataclasses import replace

import pytest

from sciloom.core.diagnostics import CompilationError, IRValidationError
from sciloom.core.ir import to_json
from . import AutoSuiteIndividualShaker, AutoSuiteTarget, write_autosuite_review
from .deployment import AutoSuiteDeploymentStatus
from .deployment_test import Configure, Stateful, empty_program, facts


def test_export_hashes_are_deterministic_and_match_written_bytes(tmp_path, monkeypatch):
    target = AutoSuiteTarget()
    result = Stateful().compile(target=target)

    def forbidden(*args, **kwargs):
        pytest.fail("Review export must not resolve or specialize again.")

    monkeypatch.setattr(AutoSuiteTarget, "resolve_devices", forbidden)
    path = tmp_path / "nested/accumulator.asfp"
    report = write_autosuite_review(result, target=target, path=path)
    assert report.status == AutoSuiteDeploymentStatus.UNKNOWN
    assert report.native_status == "pending"
    assert path.read_bytes() == result.artifact.content
    assert report.artifact_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert report.specialized_ir_sha256 == hashlib.sha256(to_json(result.specialized_ir).encode()).hexdigest()
    sidecar = path.with_suffix(".deployment.json")
    assert sidecar.read_text() == report.to_json()
    before = sidecar.read_bytes()
    assert write_autosuite_review(result, target=target, path=path) == report
    assert sidecar.read_bytes() == before
    assert json.loads(before)["native_status"] == "pending"


def test_assessment_has_no_export_hashes_and_ordinary_write_is_unchanged(tmp_path):
    target = AutoSuiteTarget(deployment=facts())
    result = Stateful().compile(target=target)
    report = target.deployment_report(result.specialized_ir)
    assert report.status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert report.artifact_sha256 is report.specialized_ir_sha256 is None
    path = result.write(tmp_path / "plain.asfp")
    assert list(tmp_path.iterdir()) == [path]
    report = write_autosuite_review(result, target=target, path=path)
    assert report.status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert report.deployment == facts()
    assert result.diagnostics == ()


@pytest.mark.parametrize("change", ["target", "bytes", "suffix", "media_type", "ir"])
def test_mismatched_result_fails_before_writing(tmp_path, change):
    target = AutoSuiteTarget()
    result = Stateful().compile(target=target)
    if change == "target":
        result = replace(result, target_id="other")
    elif change == "ir":
        result = replace(result, specialized_ir=empty_program())
    else:
        field, value = {
            "bytes": ("content", b"<functions/>"),
            "suffix": ("suffix", ".other"),
            "media_type": ("media_type", "text/plain"),
        }[change]
        result = replace(result, artifact=replace(result.artifact, **{field: value}))
    with pytest.raises(ValueError):
        write_autosuite_review(result, target=target, path=tmp_path / "new/out.asfp")
    assert not (tmp_path / "new").exists()


def test_changed_physical_profile_is_detected_even_for_configuration_only(tmp_path):
    profile = AutoSuiteIndividualShaker(zone="bench", device_id="23")
    target = AutoSuiteTarget(devices={"shaker": profile})
    result = Configure().compile(target=target)
    for alternate in (
        replace(target, devices={"shaker": replace(profile, device_id="24")}),
        replace(target, devices={"shaker": replace(profile, zone="other")}),
    ):
        with pytest.raises(ValueError, match="bindings"):
            write_autosuite_review(result, target=alternate, path=tmp_path / "out.asfp")
    with pytest.raises(CompilationError, match="missing_resource_binding"):
        write_autosuite_review(result, target=AutoSuiteTarget(), path=tmp_path / "out.asfp")
    assert not list(tmp_path.iterdir())
    write_autosuite_review(result, target=target, path=tmp_path / "out.asfp")


def test_changed_deployment_is_rechecked_before_any_output(tmp_path):
    result = Stateful().compile(target=AutoSuiteTarget())
    with pytest.raises(CompilationError, match="deployment_variable_reset"):
        write_autosuite_review(result, target=AutoSuiteTarget(deployment=facts(reset=True)), path=tmp_path / "out.asfp")
    assert not list(tmp_path.iterdir())


def test_unspecialized_device_contract_is_rejected(tmp_path):
    target = AutoSuiteTarget(devices={"shaker": AutoSuiteIndividualShaker(zone="bench", device_id="23")})
    result = Configure().compile(target=target)
    with pytest.raises(ValueError, match="concrete"):
        write_autosuite_review(
            replace(result, specialized_ir=result.semantic_ir), target=target, path=tmp_path / "out.asfp"
        )
    assert not list(tmp_path.iterdir())


def test_malformed_selected_ir_is_not_emitted(tmp_path):
    target = AutoSuiteTarget()
    result = Stateful().compile(target=target)
    result = replace(result, specialized_ir=replace(result.specialized_ir, entry_function_id="absent"))
    with pytest.raises(IRValidationError):
        write_autosuite_review(result, target=target, path=tmp_path / "out.asfp")
    assert not list(tmp_path.iterdir())


def test_device_queries_are_not_implicitly_specialized_on_export(tmp_path):
    from .portability_test import PortableAgitation, autosuite

    target = autosuite()
    result = PortableAgitation().compile(target=target)
    with pytest.raises(ValueError, match="DeviceIf"):
        write_autosuite_review(
            replace(result, specialized_ir=result.semantic_ir), target=target, path=tmp_path / "out.asfp"
        )
    assert not list(tmp_path.iterdir())


def test_io_errors_propagate_and_aliasing_paths_are_rejected(tmp_path):
    target = AutoSuiteTarget()
    result = Stateful().compile(target=target)
    parent_file = tmp_path / "file"
    parent_file.write_text("keep")
    with pytest.raises(OSError):
        write_autosuite_review(result, target=target, path=parent_file / "out.asfp")
    assert parent_file.read_text() == "keep"
    artifact = tmp_path / "alias.asfp"
    artifact.write_bytes(b"keep")
    sidecar = artifact.with_suffix(".deployment.json")
    sidecar.symlink_to(artifact)
    with pytest.raises(ValueError, match="distinct"):
        write_autosuite_review(result, target=target, path=artifact)
    assert artifact.read_bytes() == b"keep"
    sidecar.unlink()
    sidecar.mkdir()
    with pytest.raises(OSError):
        write_autosuite_review(result, target=target, path=artifact)
    assert artifact.read_bytes() == result.artifact.content  # No two-file atomicity promise.
