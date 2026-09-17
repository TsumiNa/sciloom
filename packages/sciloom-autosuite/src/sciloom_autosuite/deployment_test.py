"""Deployment assessment preserves unknown facts and never certifies execution."""

import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from sciloom import Agitator, Function, Var, rpm, runtime
from sciloom.core.ir import FunctionIR, Program, to_json
from sciloom.core.locations import LocationDirectory
from .deployment import AutoSuiteDeployment, AutoSuiteDeploymentStatus, _assess_deployment
from .layout import AutoSuiteLayout
from .layout_test import application, write_app
from .target import AutoSuiteTarget
from .xml import AutoSuiteVersion


def facts(*, reset=False, version="2.47.1.1", digest="a" * 64):
    return AutoSuiteDeployment(app_sha256=digest, product_version=version, configuration="Bench", reset_variables=reset)


def empty_program():
    return Program(entry_function_id="empty", functions=(FunctionIR(node_id="empty", name="Empty"),))


class Stateful(Function):
    counter: Var[int] = 0

    @runtime
    def run(self) -> None:
        self.counter += 1


class Configure(Function):
    shaker: Agitator

    @runtime
    def run(self) -> None:
        self.shaker.speed = 100 * rpm
        self.shaker.speed = 200 * rpm


def report(program=None, deployment=None, layout=None):
    return _assess_deployment(
        empty_program() if program is None else program,
        version=AutoSuiteVersion.V2_47_1_1,
        deployment=deployment,
        layout=layout,
    )


@pytest.mark.parametrize("setting,expected", [(None, None), ("0", False), ("1", True), (" 1\n", True)])
def test_read_exact_bytes_and_missing_settings(tmp_path, setting, expected):
    root = application()
    root.set("productversion", "2.47.1.1")
    root.set("configuration", "Bench")
    if setting is not None:
        ET.SubElement(root, "resetvariables").text = setting
    path = write_app(tmp_path, root)
    original = path.read_bytes()
    deployment = AutoSuiteDeployment.from_app(path)
    layout = AutoSuiteLayout.from_app(path)
    assert deployment.app_sha256 == layout.app_sha256 == hashlib.sha256(original).hexdigest()
    assert deployment.product_version == "2.47.1.1"
    assert deployment.configuration == "Bench"
    assert deployment.reset_variables is expected
    assert path.read_bytes() == original
    with pytest.raises(FrozenInstanceError):
        deployment.reset_variables = False


def test_unknown_product_and_configuration_are_not_fabricated(tmp_path):
    deployment = AutoSuiteDeployment.from_app(write_app(tmp_path, ET.fromstring("<application/>")))
    assert deployment.product_version is deployment.configuration is deployment.reset_variables is None
    assert report(deployment=deployment).status == AutoSuiteDeploymentStatus.UNKNOWN


def test_provenance_identifies_compressed_source_not_only_xml(tmp_path):
    path = tmp_path / "source.app"
    xml = b'<application productversion="2.47.1.1"><resetvariables>0</resetvariables></application>'
    path.write_bytes(gzip.compress(xml, mtime=1))
    first = AutoSuiteDeployment.from_app(path)
    path.write_bytes(gzip.compress(xml, mtime=2))
    second = AutoSuiteDeployment.from_app(path)
    assert first.app_sha256 != second.app_sha256
    assert first.product_version == second.product_version
    assert first.reset_variables == second.reset_variables


@pytest.mark.parametrize("value", ["", "true", "false", "2", "01", "-1"])
def test_invalid_reset_encoding_is_rejected(tmp_path, value):
    root = ET.fromstring("<application/>")
    ET.SubElement(root, "resetvariables").text = value
    with pytest.raises(ValueError, match="resetvariables"):
        AutoSuiteDeployment.from_app(write_app(tmp_path, root))


@pytest.mark.parametrize(
    "xml",
    [
        "<application><resetvariables>0</resetvariables><resetvariables>0</resetvariables></application>",
        "<application><resetvariables><value>0</value></resetvariables></application>",
        '<application><resetvariables enabled="0">1</resetvariables></application>',
        '<application productversion=" "/>',
        '<application baseapplication="other.app"/>',
        "<functions/>",
    ],
)
def test_ambiguous_or_unsupported_envelopes_are_rejected(tmp_path, xml):
    with pytest.raises(ValueError):
        AutoSuiteDeployment.from_app(write_app(tmp_path, ET.fromstring(xml)))


def test_invalid_compression_xml_and_missing_files(tmp_path):
    path = tmp_path / "bad.app"
    for data in (b"not gzip", gzip.compress(b"<broken>"), gzip.compress(b"<application/>")[:-3]):
        path.write_bytes(data)
        with pytest.raises(ValueError):
            AutoSuiteDeployment.from_app(path)
    with pytest.raises(FileNotFoundError):
        AutoSuiteDeployment.from_app(tmp_path / "missing.app")


@pytest.mark.parametrize(
    "field,value",
    [
        ("app_sha256", "invalid"),
        ("app_sha256", "A" * 64),
        ("reset_variables", 0),
        ("product_version", ""),
        ("configuration", 2),
    ],
)
def test_direct_facts_reject_invalid_values(field, value):
    with pytest.raises((TypeError, ValueError)):
        replace(facts(), **{field: value})


def test_deployment_compatibility_is_not_native_verification():
    compatible = report(deployment=facts())
    assert compatible.status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert compatible.native_status == "pending"
    assert compatible.requirements == compatible.findings == ()
    assert report(deployment=facts(reset=True)).status == AutoSuiteDeploymentStatus.COMPATIBLE
    unknown = report()
    assert unknown.status == AutoSuiteDeploymentStatus.UNKNOWN
    assert {d.code for d in unknown.findings} == {"missing_deployment"}
    incompatible = report(deployment=facts(version="9.9.9"))
    assert incompatible.status == AutoSuiteDeploymentStatus.INCOMPATIBLE
    assert "deployment_version" in {d.code for d in incompatible.findings}
    version_finding = next(d for d in incompatible.findings if d.code == "deployment_version")
    assert "'2.47.1.1'" in version_finding.message
    assert "autosuite-" not in version_finding.message
    mixed = report(deployment=facts(version="9.9.9", reset=None))
    assert mixed.status == AutoSuiteDeploymentStatus.INCOMPATIBLE
    assert {d.code for d in mixed.findings} == {"deployment_version", "unknown_variable_reset"}


def test_persistent_requirements_retain_affected_nodes_without_changing_ir():
    program = Stateful().to_ir()
    before = to_json(program)
    result = report(program, facts(reset=True))
    assert result.status == AutoSuiteDeploymentStatus.INCOMPATIBLE
    assert len(result.requirements) == 1
    requirement = result.requirements[0]
    variable = program.functions[0].variables[0]
    assert requirement.node_id == variable.node_id
    assert requirement.code == "persistent_variable"
    assert requirement.path == "$.functions[0].variables[0]"
    assert report(program, facts()).status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert report(program).status == AutoSuiteDeploymentStatus.UNKNOWN
    assert report(program, facts(reset=None)).status == AutoSuiteDeploymentStatus.UNKNOWN
    assert to_json(program) == before


def test_configuration_requirement_is_per_logical_resource():
    result = report(Configure().to_ir(), facts(reset=True))
    assert result.status == AutoSuiteDeploymentStatus.INCOMPATIBLE
    assert [d.code for d in result.requirements] == ["persistent_device_configuration"]


def test_layout_provenance_unknown_mismatch_and_same_source():
    layout = AutoSuiteLayout(elements=(), wells=(), directory=LocationDirectory())
    assert report(deployment=facts(), layout=layout).status == AutoSuiteDeploymentStatus.UNKNOWN
    known = replace(layout, app_sha256="a" * 64)
    assert report(deployment=facts(), layout=known).status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert report(deployment=facts(digest="b" * 64), layout=known).status == AutoSuiteDeploymentStatus.INCOMPATIBLE
    assert report(deployment=facts(version=None), layout=known).status == AutoSuiteDeploymentStatus.UNKNOWN
    with pytest.raises(ValueError):
        replace(layout, app_sha256="invalid")


def test_report_is_immutable_deterministic_and_explicitly_not_program_json():
    result = report(Stateful().to_ir(), facts(reset=True))
    with pytest.raises(FrozenInstanceError):
        result.status = AutoSuiteDeploymentStatus.COMPATIBLE
    with pytest.raises(TypeError):
        replace(result, findings=list(result.findings))
    encoded = result.to_json()
    assert encoded == result.to_json()
    payload = json.loads(encoded)
    assert "format_version" not in payload
    assert payload["status"] == "incompatible"
    assert payload["native_status"] == "pending"
    assert payload["deployment"]["reset_variables"] is True
    assert payload["requirements"][0]["node_id"] == result.requirements[0].node_id


def test_facts_stage_does_not_change_current_compilation():
    result = Stateful().compile(target=AutoSuiteTarget())
    assert result.artifact.suffix == ".asfp"


@pytest.mark.requires_corpus
def test_primary_app_reset_facts_are_read_only():
    path = Path(__file__).resolve().parents[4] / "autosuite/corpus/app/config20260909_polymerization.app"
    if not path.exists():
        pytest.skip("Local primary APP is absent.")
    before = path.read_bytes()
    deployment = AutoSuiteDeployment.from_app(path)
    assert deployment.product_version == "2.47.1.1"
    assert deployment.reset_variables is True
    assert deployment.app_sha256 == hashlib.sha256(before).hexdigest()
    assert path.read_bytes() == before
