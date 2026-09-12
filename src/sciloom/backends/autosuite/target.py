"""The explicit AutoSuite target: vendor legality and XML emission."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from ...core.compiler import Artifact
from ...core.diagnostics import CompilationError, Diagnostic
from ...core.ir import Binary, BinaryOp, Call, Program
from ...core.ir.traversal import iter_nodes
from .agitation import IndividualShakerBinding
from .codegen import lower_asfp
from .xml import AutoSuiteVersion


@dataclass(frozen=True, kw_only=True)
class AutoSuiteTarget:
    version: AutoSuiteVersion = AutoSuiteVersion.V2_47_1_1
    agitators: tuple[IndividualShakerBinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", AutoSuiteVersion(self.version))
        object.__setattr__(self, "agitators", tuple(self.agitators))
        logical_ids: set[str] = set()
        device_ids: set[str] = set()
        zones: set[str] = set()
        for binding in self.agitators:
            if not isinstance(binding, IndividualShakerBinding):
                raise TypeError("agitators must contain IndividualShakerBinding records.")
            if binding.logical_id in logical_ids:
                raise ValueError(f"Duplicate logical agitation binding: {binding.logical_id}")
            if binding.device_id in device_ids:
                raise ValueError(f"Distinct resources cannot alias shaker device {binding.device_id}.")
            if binding.zone in zones:
                raise ValueError(f"Distinct resources cannot bind the same AutoSuite zone {binding.zone!r}.")
            logical_ids.add(binding.logical_id)
            device_ids.add(binding.device_id)
            zones.add(binding.zone)

    @property
    def target_id(self) -> str:
        return self.version.value

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
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
        bindings = {binding.logical_id for binding in self.agitators}
        resources = {resource.logical_id for resource in program.resources}
        for i, resource in enumerate(program.resources):
            if resource.logical_id not in bindings:
                errors.append(
                    Diagnostic(
                        code="missing_resource_binding",
                        message=f"No AutoSuite binding for agitator {resource.logical_id!r}.",
                        path=f"$.resources[{i}]",
                        node_id=resource.node_id,
                        source=resource.source,
                    )
                )
        for logical_id in sorted(bindings - resources):
            errors.append(
                Diagnostic(
                    code="unknown_resource_binding",
                    message=f"AutoSuite binding {logical_id!r} has no declared resource.",
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

    def emit(self, program: Program) -> Artifact:
        serialization_ir = lower_asfp(program, self.version, agitators=self.agitators)
        try:
            content = serialization_ir.to_xml()
            ET.fromstring(content)
        except (ET.ParseError, ValueError, TypeError) as error:
            raise CompilationError((Diagnostic(code="xml_text", message=str(error), path="$"),)) from error
        return Artifact(content=content, media_type="application/xml", suffix=".asfp")
