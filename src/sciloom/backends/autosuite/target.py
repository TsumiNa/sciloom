"""The explicit AutoSuite target: vendor legality and XML emission."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from ...compiler import Artifact
from ...diagnostics import CompilationError, Diagnostic
from ...ir import Binary, BinaryOp, Call, Program
from ...ir.traversal import iter_nodes
from .lowering import lower_asfp
from .xml import AutoSuiteVersion


@dataclass(frozen=True, kw_only=True)
class AutoSuiteTarget:
    version: AutoSuiteVersion = AutoSuiteVersion.V2_47_1_1

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", AutoSuiteVersion(self.version))

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
        serialization_ir = lower_asfp(program, self.version)
        try:
            content = serialization_ir.to_xml()
            ET.fromstring(content)
        except (ET.ParseError, ValueError, TypeError) as error:
            raise CompilationError((Diagnostic(code="xml_text", message=str(error), path="$"),)) from error
        return Artifact(content=content, media_type="application/xml", suffix=".asfp")
