"""Pure device-branch selection using trusted data contracts, never Python imports."""

from dataclasses import replace
from typing import assert_never

from .bindings import DeviceBindings, validate_bindings
from .diagnostics import CompilationError, Diagnostic, IRValidationError
from .ir import (
    Assignment,
    Call,
    CanWrite,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    DeviceResource,
    If,
    IsDevice,
    ListSet,
    LogValue,
    Notify,
    Program,
    ReadWallTime,
    Resource,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    SupportsOperation,
    TimerResource,
    Wait,
    WaitUntil,
    While,
    validate,
)
from .ir.traversal import iter_nodes


def specialize(program: Program, *, bindings: DeviceBindings) -> Program:
    """Validate, select device branches and retain reachable high-level functions.

    Node identities and source spans survive selection. Resources receive trusted
    concrete interface types; deployment addresses and private backend state never
    enter this program. Missing bindings are errors even for a false device query.

    Args:
        program: Authored program; not modified by this function.
        bindings: Trusted deployment facts supplied by the selected target.

    Returns:
        A new program with selected branches and reachable functions.

    Raises:
        IRValidationError: Input or resulting semantics are invalid.
        CompilationError: Bindings are missing, incompatible or untrusted.
    """
    diagnostics = validate(program)
    if diagnostics:
        raise IRValidationError(diagnostics)
    diagnostics = validate_bindings(program, bindings)
    if diagnostics:
        raise CompilationError(diagnostics)
    deployed = {b.logical_id: b for b in bindings.devices}
    resources = {r.node_id: deployed[r.logical_id] for r in program.resources if isinstance(r, DeviceResource)}

    def block(body: tuple[Statement, ...]) -> tuple[Statement, ...]:
        selected: list[Statement] = []
        for statement in body:
            if isinstance(statement, DeviceIf):
                condition = statement.condition
                binding = resources[condition.resource_id]
                if isinstance(condition, IsDevice):
                    match = condition.device_type_id in (binding.contract.type_id, *binding.contract.base_type_ids)
                elif isinstance(condition, CanWrite):
                    match = condition.property_id in binding.writable_properties
                    expected = next(
                        p for c in program.device_types for p in c.properties if p.semantic_id == condition.property_id
                    )
                    actual = next(
                        (p for p in binding.contract.properties if p.semantic_id == condition.property_id), None
                    )
                    if match and expected != actual:
                        raise CompilationError(
                            (
                                Diagnostic(
                                    code="device_contract",
                                    message="Selected property query differs from the trusted signature.",
                                    path="$",
                                    node_id=condition.node_id,
                                    source=condition.source,
                                ),
                            )
                        )
                elif isinstance(condition, SupportsOperation):
                    match = condition.operation_id in binding.supported_operations
                    expected_command = next(
                        c for t in program.device_types for c in t.operations if c.semantic_id == condition.operation_id
                    )
                    actual_command = next(
                        (c for c in binding.contract.operations if c.semantic_id == condition.operation_id), None
                    )
                    if match and expected_command != actual_command:
                        raise CompilationError(
                            (
                                Diagnostic(
                                    code="device_contract",
                                    message="Selected command query differs from the trusted signature.",
                                    path="$",
                                    node_id=condition.node_id,
                                    source=condition.source,
                                ),
                            )
                        )
                else:
                    assert_never(condition)
                selected.extend(block(statement.then_body if match else statement.else_body))
            elif isinstance(statement, If):
                selected.append(
                    replace(statement, then_body=block(statement.then_body), else_body=block(statement.else_body))
                )
            elif isinstance(statement, While):
                selected.append(replace(statement, body=block(statement.body)))
            elif isinstance(
                statement,
                (
                    Assignment,
                    ListSet,
                    LogValue,
                    Notify,
                    ReadWallTime,
                    Wait,
                    StartTimer,
                    WaitUntil,
                    Call,
                    ConfigureProperty,
                    StartAgitation,
                    StopAgitation,
                    DeviceCommand,
                ),
            ):
                selected.append(statement)
            else:
                assert_never(statement)
        return tuple(selected)

    functions = {f.node_id: replace(f, body=block(f.body)) for f in program.functions}
    reachable: set[str] = set()
    pending = [program.entry_function_id]
    while pending:
        function_id = pending.pop()
        if function_id in reachable:
            continue
        reachable.add(function_id)
        pending.extend(n.function_id for n, _ in iter_nodes(functions[function_id]) if isinstance(n, Call))
    # DeviceIf is gone: only trusted bound interfaces/ancestors are needed now.
    # Inactive extension declarations remain exclusively in the authored program.
    directory = {}
    for binding in bindings.devices:
        for contract in (*binding.base_contracts, binding.contract):
            directory[contract.type_id] = contract
    selected_resources: list[Resource] = []
    for resource in program.resources:
        if isinstance(resource, DeviceResource):
            selected_resources.append(replace(resource, device_type_id=resources[resource.node_id].contract.type_id))
        elif isinstance(resource, TimerResource):
            if resource.owner_id in reachable:
                selected_resources.append(resource)
        else:
            assert_never(resource)
    result = replace(
        program,
        functions=tuple(functions[f.node_id] for f in program.functions if f.node_id in reachable),
        resources=tuple(selected_resources),
        device_types=tuple(directory[key] for key in sorted(directory)),
    )
    diagnostics = validate(result)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return result
