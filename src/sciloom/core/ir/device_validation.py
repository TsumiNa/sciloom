"""Validate device directories and high-level device syntax without deployments."""

import re
from typing import Callable

from .device_contracts import (
    AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT, AGITATOR_TYPE_ID,
    PropertyContract, CommandContract, DeviceTypeContract,
)
from .model import DeviceResource, Node, Program

Report = Callable[[str, str, str, Node | None], None]


def validate_directory(program: Program, report: Report) -> None:
    types: dict[str, DeviceTypeContract] = {}
    members: dict[str, PropertyContract | CommandContract] = {}
    builtin_members: tuple[PropertyContract | CommandContract, ...] = (*AGITATOR_CONTRACT.properties, *AGITATOR_CONTRACT.operations)
    builtins = {p.semantic_id: p for p in builtin_members}
    for i, contract in enumerate(program.device_types):
        path = f"$.device_types[{i}]"
        if not semantic_id(contract.type_id) or contract.type_id in types:
            report("device_contract", "Device type IDs must be unique, namespaced and versioned.", path, None)
        types[contract.type_id] = contract
        if contract.type_id in contract.base_type_ids or len(set(contract.base_type_ids)) != len(contract.base_type_ids):
            report("device_contract", "Device ancestry must be distinct and cannot contain itself.", path, None)
        names: set[str] = set()
        declarations: tuple[PropertyContract | CommandContract, ...] = (*contract.properties, *contract.operations)
        for member in declarations:
            if not semantic_id(member.semantic_id) or not member.name.isidentifier() or member.name in names:
                report("device_contract", "Device members need unique names and versioned semantic IDs.", path, None)
            names.add(member.name)
            if member.semantic_id in members and members[member.semantic_id] != member:
                report("device_contract", "A semantic member ID cannot describe different signatures.", path, None)
            if member.semantic_id in builtins and member != builtins[member.semantic_id]:
                report("device_contract", "Built-in member signatures cannot be redefined.", path, None)
            members[member.semantic_id] = member
            if isinstance(member, CommandContract):
                parameter_names = [p.name for p in member.parameters]
                if len(set(parameter_names)) != len(parameter_names) or any(not n.isidentifier() for n in parameter_names):
                    report("device_contract", "Command parameter names must be unique identifiers.", path, None)
        properties = {p.semantic_id for p in contract.properties}
        if len(set(contract.required_configuration)) != len(contract.required_configuration) or not set(contract.required_configuration) <= properties:
            report("device_contract", "Required configuration must identify distinct declared properties.", path, None)
    for contract in program.device_types:
        for base_id in contract.base_type_ids:
            base = types.get(base_id)
            if base is None or contract.type_id in base.base_type_ids:
                report("device_contract", "Device ancestry must reference existing, acyclic type contracts.", "$.device_types", None)
            elif not set(base.base_type_ids) <= set(contract.base_type_ids):
                report("device_contract", "Device ancestry must include the complete base-type closure.", "$.device_types", None)
            elif any(p not in contract.properties for p in base.properties) or any(op not in contract.operations for op in base.operations):
                report("device_contract", "Inherited member signatures cannot be removed or changed.", "$.device_types", None)
    for builtin in (BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT):
        if builtin.type_id in types and types[builtin.type_id] != builtin:
            report("device_contract", "Built-in semantic contracts cannot be redefined.", "$.device_types", None)
    for resource in program.resources:
        if resource.device_type_id not in types:
            report("device_contract", "Device resources must reference a declared type contract.", "$.resources", resource)


def semantic_id(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]+/v[1-9][0-9]*", value) is not None


def members_for(program: Program, resource: DeviceResource) -> tuple[tuple[PropertyContract, ...], tuple[CommandContract, ...]]:
    """Include explicitly catalogued extensions of the declared category.

    Binding validation proves that selected members are implemented. Merely
    sharing a spelling with a member of an unrelated category is insufficient.
    """
    related = [c for c in program.device_types if resource.device_type_id in (c.type_id, *c.base_type_ids)]
    return tuple(p for c in related for p in c.properties), tuple(op for c in related for op in c.operations)


def is_agitator(program: Program, resource: DeviceResource) -> bool:
    return any(c.type_id == resource.device_type_id and AGITATOR_TYPE_ID in (c.type_id, *c.base_type_ids) for c in program.device_types)
