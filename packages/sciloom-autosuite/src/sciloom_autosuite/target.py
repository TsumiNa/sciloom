"""The explicit AutoSuite target: vendor legality and XML emission."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import Artifact
from sciloom.core.diagnostics import CompilationError, Diagnostic
from sciloom.core.ir import Binary, BinaryOp, Call, DeviceAt, Program
from sciloom.core.ir.traversal import iter_nodes
from .agitation import AutoSuiteIndividualShaker
from .codegen import lower_asfp
from .deployment import AutoSuiteDeployment, AutoSuiteDeploymentReport, AutoSuiteDeploymentStatus, _assess_deployment
from .layout import AutoSuiteLayout
from .selection import AutoSuiteAgitatorSelection, profile_binding
from .timing import validate_timer_scopes
from .validation import validate_array_outputs, validate_runtime_guards
from .well_properties import validate_well_properties
from .xml import AutoSuiteVersion


@dataclass(frozen=True, kw_only=True)
class AutoSuiteTarget:
    """Compile validated SciLoom programs to AutoSuite function-package XML.

    Args:
        version: Supported AutoSuite serialization profile.
        devices: Logical paths mapped to fixed shakers or bounded candidate selections.
        layout: Read-only APP deployment facts. Required for candidate selection;
            when supplied, also validates fixed profiles against real well ancestry.
        deployment: Optional APP settings. Known incompatibilities reject compilation;
            missing facts retain offline generation with an unknown deployment report.

    Raises:
        TypeError: A binding, layout or deployment has an unsupported record type.
        ValueError: A profile/version/path is invalid, physical bindings overlap,
            or layout facts do not resolve the declared controller and wells.

    Dynamic selection is representable and validated, but compilation reports
    unsupported_device_location until native failure guards have been verified.
    Generated XML still requires AutoSuite Executor validation on the deployment host."""

    version: AutoSuiteVersion = AutoSuiteVersion.V2_47_1_1
    devices: Mapping[str, AutoSuiteIndividualShaker | AutoSuiteAgitatorSelection] = field(default_factory=dict)
    layout: AutoSuiteLayout | None = None
    deployment: AutoSuiteDeployment | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", AutoSuiteVersion(self.version))
        object.__setattr__(self, "devices", MappingProxyType(dict(self.devices)))
        if self.layout is not None and type(self.layout) is not AutoSuiteLayout:
            raise TypeError("layout must be an AutoSuiteLayout.")
        if self.deployment is not None and type(self.deployment) is not AutoSuiteDeployment:
            raise TypeError("deployment must be an AutoSuiteDeployment.")
        device_ids: set[str] = set()
        zones: set[str] = set()
        for name, binding in self.devices.items():
            if (
                not isinstance(name, str)
                or not name
                or any(not part.isidentifier() or part.startswith("_") for part in name.split("."))
            ):
                raise ValueError("Device binding names must be logical field/component paths.")
            if type(binding) not in (AutoSuiteIndividualShaker, AutoSuiteAgitatorSelection):
                raise TypeError("devices must contain AutoSuiteIndividualShaker or AutoSuiteAgitatorSelection records.")
            profiles = (binding,) if isinstance(binding, AutoSuiteIndividualShaker) else binding.candidates
            for profile in profiles:
                if profile.device_id in device_ids:
                    raise ValueError(f"Distinct resources cannot alias shaker device {profile.device_id}.")
                if profile.zone in zones:
                    raise ValueError(f"Distinct resources cannot bind the same AutoSuite zone {profile.zone!r}.")
                device_ids.add(profile.device_id)
                zones.add(profile.zone)
            profile_binding(name, binding, self.layout)

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Translate explicit deployment profiles into trusted, contributor-neutral facts."""
        return DeviceBindings(
            devices=tuple(profile_binding(name, device, self.layout) for name, device in sorted(self.devices.items()))
        )

    @property
    def target_id(self) -> str:
        """Return the selected AutoSuite format identity."""
        return self.version.value

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """Return platform and deployment diagnostics for specialized IR.

        Args:
            program: Structurally valid, specialized semantic IR.

        Returns:
            An empty tuple when the currently implemented target checks pass."""
        calls = {
            f.node_id: [(n, p) for n, p in iter_nodes(f, f"$.functions[{i}]") if isinstance(n, Call)]
            for i, f in enumerate(program.functions)
        }
        errors = [
            Diagnostic(
                code="unsupported_short_circuit",
                message="AutoSuite short-circuit equivalence is unverified; lower to explicit If statements.",
                path=path,
                node_id=node.node_id,
                source=node.source,
            )
            for node, path in iter_nodes(program)
            if isinstance(node, Binary) and node.op in (BinaryOp.AND, BinaryOp.OR)
        ]
        errors.extend(validate_array_outputs(program))
        errors.extend(validate_runtime_guards(program))
        errors.extend(validate_timer_scopes(program))
        errors.extend(validate_well_properties(program))
        deployment = self.deployment_report(program)
        if deployment.status == AutoSuiteDeploymentStatus.INCOMPATIBLE:
            errors.extend(deployment.findings)
            if any(finding.code == "deployment_variable_reset" for finding in deployment.findings):
                errors.extend(deployment.requirements)
        if any(isinstance(profile, AutoSuiteAgitatorSelection) for profile in self.devices.values()) and not any(
            isinstance(node, DeviceAt) for node, _ in iter_nodes(program)
        ):
            errors.append(
                Diagnostic(
                    code="unsupported_device_location",
                    message="AutoSuite candidate deployment requires verified runtime selection guards before emission.",
                    path="$.resources",
                )
            )
        completed: set[str] = set()
        for root in calls:
            if root in completed:
                continue
            active = {root}
            stack = [(root, iter(calls[root]))]
            while stack:
                current, edges = stack[-1]
                edge = next(edges, None)
                if edge is None:
                    active.remove(current)
                    completed.add(current)
                    stack.pop()
                    continue
                call, path = edge
                if call.function_id in active:
                    errors.append(
                        Diagnostic(
                            code="recursive_call",
                            message="AutoSuite does not support recursive calls.",
                            path=path,
                            node_id=call.node_id,
                            source=call.source,
                        )
                    )
                elif call.function_id not in completed:
                    active.add(call.function_id)
                    stack.append((call.function_id, iter(calls[call.function_id])))
        return tuple(errors)

    def deployment_report(self, program: Program) -> AutoSuiteDeploymentReport:
        """Assess deployment conditions without resolving, specializing or executing.

        Args:
            program: Validated, already-specialized IR, typically from CompileResult.

        Returns:
            Requirements and checked facts. Compatible never certifies native execution.
        """
        return _assess_deployment(program, version=self.version, deployment=self.deployment, layout=self.layout)

    def emit(self, program: Program) -> Artifact:
        """Generate an ASFP artifact from a validated, specialized program.

        Args:
            program: IR already checked by the public compilation pipeline.

        Returns:
            UTF-8 XML bytes with application/xml media type and .asfp suffix.

        Raises:
            CompilationError: Generation cannot represent the program or produce valid XML.

        Use compile_ir or Function.compile to run all preceding validation stages."""
        fixed: dict[str, AutoSuiteIndividualShaker] = {}
        for name, profile in self.devices.items():
            if not isinstance(profile, AutoSuiteIndividualShaker):
                raise CompilationError(
                    (
                        Diagnostic(
                            code="unsupported_device_location",
                            message="Unchecked dynamic device emission is not supported.",
                            path="$.resources",
                        ),
                    )
                )
            fixed[name] = profile
        serialization_ir = lower_asfp(program, self.version, devices=fixed)
        try:
            content = serialization_ir.to_xml()
            ET.fromstring(content)
        except (ET.ParseError, ValueError, TypeError) as error:
            raise CompilationError((Diagnostic(code="xml_text", message=str(error), path="$"),)) from error
        return Artifact(content=content, media_type="application/xml", suffix=".asfp")
