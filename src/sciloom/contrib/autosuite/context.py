"""Target names, stable identities and deployment state for one emission."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from uuid import UUID, uuid5
from ...core.ir import (
    Program,
    FunctionIR,
    ListType,
    ListLiteral,
    Literal,
    ScalarType,
    ValueType,
    Variable,
    VariableRole,
)
from ...core.ir.traversal import iter_nodes
from .agitation import AutoSuiteIndividualShaker
from .xml import XmlNode, xml_node as _xml

if TYPE_CHECKING:
    from .device_state import DeviceStorage


class CodegenContext:
    def __init__(self, package: Program, namespace: UUID, resources: dict[str, AutoSuiteIndividualShaker]) -> None:
        self.package = package
        self.namespace = namespace
        self.resources = resources
        self.device_state: dict[str, dict[str, DeviceStorage]] = {}
        self.functions = {function.node_id: function for function in package.functions}
        self.variables = {v.node_id: v for f in package.functions for v in f.variables}
        self.names: dict[str, str] = {}
        for function in package.functions:
            used: set[str] = set()
            for i, variable in enumerate(function.variables):
                # The manual requires an ASCII letter as the first character.
                candidate = variable.name if re.fullmatch(r"[A-Za-z][A-Za-z_0-9]*", variable.name) else f"v_{i}"
                if candidate.lower() in {"true", "false", "not", "and", "or"}:
                    candidate = f"v_{i}"
                while candidate in used:
                    candidate += "_"
                used.add(candidate)
                self.names[variable.node_id] = candidate
        self.parameter_names = self.names.copy()
        self.temporaries: dict[str, list[Variable]] = {f.node_id: [] for f in package.functions}
        self.sequence = 0
        self.occupied_ids = {node.node_id for node, _ in iter_nodes(package)}

    def fresh_id(self) -> str:
        while True:
            self.sequence += 1
            identity = f"generated:{self.sequence}"
            if identity not in self.occupied_ids:
                self.occupied_ids.add(identity)
                return identity

    def temporary(self, function: FunctionIR, value_type: ValueType, *, length: int = 0) -> str:
        """Allocate target-owned storage without adding nodes to the semantic program."""
        identity = self.fresh_id()
        occupied = {self.names[v.node_id] for v in function.variables}
        occupied.update(self.parameter_names[v.node_id] for v in function.variables)
        occupied.update(self.names[v.node_id] for v in self.temporaries[function.node_id])
        name = f"sciloom_tmp_{self.sequence}"
        while name in occupied:
            name += "_"
        scalar = value_type.element_type if isinstance(value_type, ListType) else value_type
        zero = False if scalar == ScalarType.BOOLEAN else 0
        initial = (
            ListLiteral(
                node_id=identity + ":initial",
                type=value_type,
                elements=tuple(
                    Literal(node_id=f"{identity}:initial:{i}", type=scalar, value=zero) for i in range(length)
                ),
            )
            if isinstance(value_type, ListType)
            else Literal(node_id=identity + ":initial", type=scalar, value=zero)
        )
        variable = Variable(
            node_id=identity,
            owner_id=function.node_id,
            name=name,
            role=VariableRole.INTERNAL,
            type=value_type,
            initial=initial,
        )
        self.names[identity] = name
        self.temporaries[function.node_id].append(variable)
        return name

    def identifier(self, role: str, semantic_id: str) -> str:
        return "{" + str(uuid5(self.namespace, json.dumps((role, semantic_id)))).upper() + "}"

    def metadata(self, name: str, *, expanded: bool = False) -> list[XmlNode]:
        # Fixed epoch metadata makes recompilation reproducible; it is not execution state.
        result = [_xml("description"), _xml("name", name), _xml("edittime", "0")]
        if expanded:
            result.append(_xml("expanded", "1"))
        return result
