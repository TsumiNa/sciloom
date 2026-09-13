"""The explicit AutoSuite target: vendor legality and XML emission."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from ...core.compiler import Artifact
from ...core.devices import DeviceBindings
from ...core.diagnostics import CompilationError, Diagnostic
from ...core.ir import Binary, BinaryOp, Call, Program
from ...core.ir.traversal import iter_nodes
from ...devices.declarations import bind_device
from .agitation import AutoSuiteIndividualShaker
from .codegen import lower_asfp
from .xml import AutoSuiteVersion
from .validation import validate_array_outputs


@dataclass(frozen=True, kw_only=True)
class AutoSuiteTarget:
    """Compile validated SciLoom programs to AutoSuite function-package XML.
    
    Args:
        version: Supported AutoSuite serialization profile.
        devices: Logical field/component paths mapped to individual shaker profiles.
    
    Raises:
        TypeError: A binding is not an AutoSuiteIndividualShaker.
        ValueError: A profile/version/path is invalid or physical bindings are duplicated.
    
    Generated XML still requires AutoSuite Executor validation on the deployment host."""
    version: AutoSuiteVersion = AutoSuiteVersion.V2_47_1_1
    devices: Mapping[str, AutoSuiteIndividualShaker] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", AutoSuiteVersion(self.version))
        object.__setattr__(self, "devices", MappingProxyType(dict(self.devices)))
        device_ids: set[str] = set()
        zones: set[str] = set()
        for name, binding in self.devices.items():
            if not isinstance(name, str) or not name or any(
                not part.isidentifier() or part.startswith("_") for part in name.split(".")
            ):
                raise ValueError("Device binding names must be logical field/component paths.")
            if type(binding) is not AutoSuiteIndividualShaker:
                raise TypeError("devices must contain AutoSuiteIndividualShaker records.")
            if binding.device_id in device_ids:
                raise ValueError(f"Distinct resources cannot alias shaker device {binding.device_id}.")
            if binding.zone in zones:
                raise ValueError(f"Distinct resources cannot bind the same AutoSuite zone {binding.zone!r}.")
            device_ids.add(binding.device_id)
            zones.add(binding.zone)

    def resolve_devices(self, program: Program) -> DeviceBindings:
        """Translate explicit deployment profiles into trusted, contributor-neutral facts."""
        return DeviceBindings(
            devices=tuple(
                bind_device(
                    logical_id=name,
                    device=device,
                    physical_id=f"autosuite:individual-shaker:{device.device_id}",
                )
                for name, device in sorted(self.devices.items())
            )
        )

    @property
    def target_id(self) -> str:
        """Return the selected AutoSuite format identity."""
        return self.version.value

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        """Return platform diagnostics for recursion, Boolean operations and array outputs.
        
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

    def emit(self, program: Program) -> Artifact:
        """Generate an ASFP artifact from a validated, specialized program.
        
        Args:
            program: IR already checked by the public compilation pipeline.
        
        Returns:
            UTF-8 XML bytes with application/xml media type and .asfp suffix.
        
        Raises:
            CompilationError: Generation cannot represent the program or produce valid XML.
        
        Use compile_ir or Function.compile to run all preceding validation stages."""
        serialization_ir = lower_asfp(program, self.version, devices=self.devices)
        try:
            content = serialization_ir.to_xml()
            ET.fromstring(content)
        except (ET.ParseError, ValueError, TypeError) as error:
            raise CompilationError((Diagnostic(code="xml_text", message=str(error), path="$"),)) from error
        return Artifact(content=content, media_type="application/xml", suffix=".asfp")
