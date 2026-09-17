"""Read-only APP settings and explicit, non-execution deployment assessments."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zlib
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal as TypingLiteral

from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import ConfigureProperty, Program, Variable, VariableRole
from sciloom.core.ir.traversal import iter_nodes
from .layout import AutoSuiteLayout
from .xml import AutoSuiteVersion


@dataclass(frozen=True, kw_only=True)
class AutoSuiteDeployment:
    """Observed application settings, independent of its spatial layout.

    Attributes:
        app_sha256: Lowercase SHA-256 of the exact compressed source bytes.
        product_version: Native product version, or None when not recorded.
        configuration: Optional display label, not a globally unique identity.
        reset_variables: Native Macro re-entry reset setting; None means unknown.

    Raises:
        TypeError: A setting has the wrong type.
        ValueError: A hash or supplied label is malformed.

    These facts do not certify Executor behavior or configure any equipment.
    """

    app_sha256: str
    product_version: str | None = None
    configuration: str | None = None
    reset_variables: bool | None = None

    def __post_init__(self) -> None:
        if type(self.app_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", self.app_sha256) is None:
            raise ValueError("app_sha256 must be a lowercase SHA-256 digest.")
        for name in ("product_version", "configuration"):
            value = getattr(self, name)
            if value is not None:
                if type(value) is not str:
                    raise TypeError(f"{name} must be text or None.")
                if not value.strip():
                    raise ValueError(f"{name} must be nonempty when supplied.")
        if self.reset_variables is not None and type(self.reset_variables) is not bool:
            raise TypeError("reset_variables must be bool or None, never an integer default.")

    @classmethod
    def from_app(cls, path: str | Path) -> AutoSuiteDeployment:
        """Read a standalone gzip APP without loading tasks or writing its bytes.

        Args:
            path: Existing compressed application file.

        Returns:
            Immutable observed facts. Absent version/reset fields remain unknown.

        Raises:
            OSError: The source cannot be read.
            ValueError: Compression/XML is invalid, the APP depends on an external
                base application, or a recorded setting is malformed/ambiguous.

        Unsupported product versions are retained for assessment, not accepted
        as supported profiles. Only the direct application reset field is read.
        """
        payload = Path(path).read_bytes()
        try:
            root = ET.fromstring(gzip.decompress(payload))
        except (OSError, EOFError, zlib.error, ET.ParseError) as error:
            raise ValueError(f"Expected a gzip-compressed AutoSuite APP: {error}") from error
        if root.tag != "application" or root.get("baseapplication", "").strip():
            raise ValueError("Read a standalone application with no unresolved base application.")
        resets = root.findall("resetvariables")
        if len(resets) > 1:
            raise ValueError("APP has ambiguous duplicate resetvariables settings.")
        reset = None
        if resets:
            node = resets[0]
            value = (node.text or "").strip()
            if node.attrib or len(node) or value not in ("0", "1"):
                raise ValueError("APP resetvariables must be a single unstructured 0 or 1.")
            reset = value == "1"
        return cls(
            app_sha256=hashlib.sha256(payload).hexdigest(),
            product_version=root.get("productversion"),
            configuration=root.get("configuration"),
            reset_variables=reset,
        )


class AutoSuiteDeploymentStatus(StrEnum):
    """Result of checking known deployment conditions, never native execution."""

    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True)
class AutoSuiteDeploymentReport:
    """Immutable deployment requirements and facts with a separate native status.

    Attributes:
        status: Compatibility of checked settings; unknown information never passes.
        target_id: Selected serialization target identity.
        deployment: Observed application facts, absent for offline assessment.
        layout_app_sha256: Layout source provenance when supplied and known.
        requirements: Ordered conditions with affected semantic nodes and paths.
        findings: Incompatibilities or missing facts, separate from requirements.
        artifact_sha256: Exact artifact digest after checked review export, else None.
        specialized_ir_sha256: Canonical selected Program digest after export, else None.

    Compatible means only the documented checks passed. It is not permission to
    execute hardware or proof of Executor acceptance. Reports are not Program JSON.
    """

    status: AutoSuiteDeploymentStatus
    target_id: str
    deployment: AutoSuiteDeployment | None
    layout_app_sha256: str | None = None
    requirements: tuple[Diagnostic, ...] = ()
    findings: tuple[Diagnostic, ...] = ()
    artifact_sha256: str | None = None
    specialized_ir_sha256: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", AutoSuiteDeploymentStatus(self.status))
        if type(self.target_id) is not str or not self.target_id.strip():
            raise ValueError("Report target_id must be nonempty text.")
        if self.deployment is not None and type(self.deployment) is not AutoSuiteDeployment:
            raise TypeError("Report deployment must be AutoSuiteDeployment or None.")
        for name in ("layout_app_sha256", "artifact_sha256", "specialized_ir_sha256"):
            value = getattr(self, name)
            if value is not None and (type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None):
                raise ValueError(f"Report {name} must be a lowercase SHA-256 digest or None.")
        for name in ("requirements", "findings"):
            values = getattr(self, name)
            if type(values) is not tuple or any(type(value) is not Diagnostic for value in values):
                raise TypeError(f"Report {name} must be an immutable tuple of Diagnostic records.")

    @property
    def native_status(self) -> TypingLiteral["pending"]:
        """Keep native acceptance pending; this assessment runs no Executor."""
        return "pending"

    def to_json(self) -> str:
        """Return deterministic review data, with no Program format-version claim.

        Returns:
            UTF-8-compatible JSON text ending in a newline. Recorded source paths
            belong to supplied diagnostics; no timestamp or host path is sampled.
        """
        return (
            json.dumps(
                {**asdict(self), "native_status": self.native_status}, ensure_ascii=False, sort_keys=True, indent=2
            )
            + "\n"
        )


def _assess_deployment(
    program: Program,
    *,
    version: AutoSuiteVersion,
    deployment: AutoSuiteDeployment | None,
    layout: AutoSuiteLayout | None,
) -> AutoSuiteDeploymentReport:
    """Assess validated, specialized IR without reading files or binding devices."""
    requirements: list[Diagnostic] = []
    configured: set[str] = set()
    for node, path in iter_nodes(program):
        if isinstance(node, Variable) and node.role == VariableRole.INTERNAL:
            requirements.append(
                Diagnostic(
                    code="persistent_variable",
                    message=f"Variable {node.name!r} requires state to persist across calls; Macro re-entry reset must be disabled.",
                    path=path,
                    node_id=node.node_id,
                    source=node.source,
                )
            )
        elif isinstance(node, ConfigureProperty) and node.resource_id not in configured:
            configured.add(node.resource_id)
            requirements.append(
                Diagnostic(
                    code="persistent_device_configuration",
                    message=f"Saved configuration for resource {node.resource_id!r} requires persistent call storage; Macro re-entry reset must be disabled.",
                    path=path,
                    node_id=node.node_id,
                    source=node.source,
                )
            )
    findings: list[Diagnostic] = []
    incompatible = False
    if deployment is None:
        findings.append(
            Diagnostic(
                code="missing_deployment",
                message="No APP was supplied; deployment conditions are unchecked.",
                path="$.deployment",
            )
        )
    else:
        expected_version = version.value.removeprefix("autosuite-")
        if deployment.product_version is None:
            findings.append(
                Diagnostic(
                    code="unknown_deployment_version",
                    message="The APP does not record its product version.",
                    path="$.deployment.product_version",
                )
            )
        elif deployment.product_version != expected_version:
            incompatible = True
            findings.append(
                Diagnostic(
                    code="deployment_version",
                    message=f"APP product version {deployment.product_version!r} does not match expected product version {expected_version!r}.",
                    path="$.deployment.product_version",
                )
            )
        if deployment.reset_variables is None:
            findings.append(
                Diagnostic(
                    code="unknown_variable_reset",
                    message="APP Macro variable-reset behavior is not recorded.",
                    path="$.deployment.reset_variables",
                )
            )
        elif deployment.reset_variables and requirements:
            incompatible = True
            findings.append(
                Diagnostic(
                    code="deployment_variable_reset",
                    message="APP resets Macro variables on re-entry, conflicting with the listed persistent-state requirements.",
                    path="$.deployment.reset_variables",
                )
            )
        if layout is not None:
            if layout.app_sha256 is None:
                findings.append(
                    Diagnostic(
                        code="unknown_layout_provenance",
                        message="Layout source provenance is unknown; it cannot be matched to the APP settings.",
                        path="$.layout.app_sha256",
                    )
                )
            elif layout.app_sha256 != deployment.app_sha256:
                incompatible = True
                findings.append(
                    Diagnostic(
                        code="deployment_source_mismatch",
                        message="Layout and deployment settings came from different APP bytes.",
                        path="$.layout.app_sha256",
                    )
                )
    status = (
        AutoSuiteDeploymentStatus.INCOMPATIBLE
        if incompatible
        else AutoSuiteDeploymentStatus.UNKNOWN
        if findings
        else AutoSuiteDeploymentStatus.COMPATIBLE
    )
    return AutoSuiteDeploymentReport(
        status=status,
        target_id=version.value,
        deployment=deployment,
        layout_app_sha256=None if layout is None else layout.app_sha256,
        requirements=tuple(requirements),
        findings=tuple(findings),
    )
