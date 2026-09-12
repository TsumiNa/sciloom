"""Target names, stable identities and deployment state for one emission."""

from __future__ import annotations

import json
import re
from uuid import UUID, uuid5
from ...core.ir import Program
from .agitation import IndividualShakerBinding
from .xml import XmlNode, xml_node as _xml


class CodegenContext:
    def __init__(self, package: Program, namespace: UUID, resources: dict[str, IndividualShakerBinding]) -> None:
        self.package = package
        self.namespace = namespace
        self.resources = resources
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

    def identifier(self, role: str, semantic_id: str) -> str:
        return "{" + str(uuid5(self.namespace, json.dumps((role, semantic_id)))).upper() + "}"

    def metadata(self, name: str, *, expanded: bool = False) -> list[XmlNode]:
        # Fixed epoch metadata makes recompilation reproducible; it is not execution state.
        result = [_xml("description"), _xml("name", name), _xml("edittime", "0")]
        if expanded:
            result.append(_xml("expanded", "1"))
        return result
