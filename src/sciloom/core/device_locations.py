"""Prove lexical device-selection scope across calls without historical context."""

from typing import assert_never

from .bindings import DeviceBindings, DeviceSelectionBinding
from .diagnostics import Diagnostic
from .ir import (
    AppendCsv,
    AskYesNo,
    Assignment,
    Call,
    ConfigureProperty,
    DeviceAt,
    DeviceCommand,
    DeviceIf,
    DeviceResource,
    ForEachZone,
    If,
    ListSet,
    Literal,
    LogValue,
    Notify,
    Program,
    ReadCsv,
    ReadWallTime,
    ReadWellProperty,
    RequestText,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    Wait,
    WaitUntil,
    While,
    WriteWellProperty,
    ZoneLiteral,
)
from .ir.device_contracts import HEATER_TYPE_ID
from .ir.traversal import iter_nodes


def validate_device_locations(program: Program, bindings: DeviceBindings) -> tuple[Diagnostic, ...]:
    """Check compatible bindings, inherited scopes and same-resource nesting.

    Input must already be structurally valid and specialized with complete
    bindings. Scope requirements and possible openings are monotone summaries;
    recursion cannot hide a nested selection or manufacture an entry context.
    Configuration writes save logical values and do not require a selection.
    """
    deployed = {b.logical_id: b for b in bindings.devices}
    dynamic = {
        r.node_id
        for r in program.resources
        if isinstance(r, DeviceResource) and isinstance(deployed[r.logical_id], DeviceSelectionBinding)
    }
    required: dict[str, set[str]] = {f.node_id: set() for f in program.functions}
    opened: dict[str, set[str]] = {f.node_id: set() for f in program.functions}
    commands = {
        node.node_id: (node, path)
        for node, path in iter_nodes(program)
        if isinstance(node, (StartAgitation, StopAgitation, DeviceCommand))
    }
    errors: list[Diagnostic] = [
        Diagnostic(
            code="unsupported_thermal_selection",
            message="Heater currently requires a fixed DeviceBinding; dynamic thermal selection is unsupported.",
            path=f"$.resources[{i}]",
            node_id=resource.node_id,
            source=resource.source,
        )
        for i, resource in enumerate(program.resources)
        if isinstance(resource, DeviceResource)
        and resource.node_id in dynamic
        and HEATER_TYPE_ID
        in (
            deployed[resource.logical_id].contract.type_id,
            *deployed[resource.logical_id].contract.base_type_ids,
        )
    ]

    def block(body: tuple[Statement, ...], active: set[str], path: str, report: bool) -> tuple[set[str], set[str]]:
        needs: set[str] = set()
        opens: set[str] = set()
        for index, node in enumerate(body):
            p = f"{path}[{index}]"
            code = message = ""
            if isinstance(node, DeviceAt):
                opens.add(node.resource_id)
                if node.resource_id not in dynamic:
                    code, message = (
                        "device_selection_binding",
                        "at() requires an explicit candidate selection binding, including for one controller.",
                    )
                elif node.resource_id in active:
                    code, message = (
                        "device_selection_nesting",
                        "The same logical resource cannot have nested location scopes.",
                    )
                child_needs, child_opens = block(node.body, active | {node.resource_id}, f"{p}.body", report)
                needs |= child_needs
                opens |= child_opens
            elif isinstance(node, Call):
                needs |= {
                    identity
                    for identity in required[node.function_id]
                    if commands[identity][0].resource_id not in active
                }
                opens |= opened[node.function_id]
                if active & opened[node.function_id]:
                    code, message = (
                        "device_selection_nesting",
                        "A called Function may select a resource whose location is already active.",
                    )
            elif isinstance(node, (StartAgitation, StopAgitation, DeviceCommand)):
                if node.resource_id in dynamic and node.resource_id not in active:
                    needs.add(node.node_id)
            elif isinstance(node, If):
                branches: tuple[tuple[str, tuple[Statement, ...]], ...] = (
                    ("then_body", node.then_body),
                    ("else_body", node.else_body),
                )
                if isinstance(node.condition, Literal):
                    branches = (branches[0] if node.condition.value else branches[1],)
                for label, branch in branches:
                    child_needs, child_opens = block(branch, active, f"{p}.{label}", report)
                    needs |= child_needs
                    opens |= child_opens
            elif isinstance(node, (While, ForEachZone)):
                skipped = (
                    isinstance(node, While)
                    and isinstance(node.condition, Literal)
                    and node.condition.value is False
                    or isinstance(node, ForEachZone)
                    and isinstance(node.value, ZoneLiteral)
                    and not node.value.well_ids
                )
                if not skipped:
                    child_needs, child_opens = block(node.body, active, f"{p}.body", report)
                    needs |= child_needs
                    opens |= child_opens
            elif isinstance(node, DeviceIf):
                raise AssertionError("Specialize device queries before checking location scopes.")
            elif isinstance(
                node,
                (
                    AppendCsv,
                    Assignment,
                    ConfigureProperty,
                    ListSet,
                    LogValue,
                    Notify,
                    ReadCsv,
                    ReadWallTime,
                    RequestText,
                    AskYesNo,
                    ReadWellProperty,
                    WriteWellProperty,
                    StartTimer,
                    Wait,
                    WaitUntil,
                ),
            ):
                pass
            else:
                assert_never(node)
            if report and code:
                errors.append(Diagnostic(code=code, message=message, path=p, node_id=node.node_id, source=node.source))
        return needs, opens

    changed = True
    while changed:
        changed = False
        for function in program.functions:
            needs, opens = block(function.body, set(), "$", False)
            if needs != required[function.node_id] or opens != opened[function.node_id]:
                required[function.node_id], opened[function.node_id] = needs, opens
                changed = True
    for index, function in enumerate(program.functions):
        block(function.body, set(), f"$.functions[{index}].body", True)
    for identity, (node, path) in commands.items():
        if identity not in required[program.entry_function_id]:
            continue
        errors.append(
            Diagnostic(
                code="device_selection_required",
                message="A dynamically bound device command needs an active at() scope on every reachable path.",
                path=path,
                node_id=node.node_id,
                source=node.source,
            )
        )
    return tuple(errors)
