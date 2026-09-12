"""Capability checks and interprocedural definite device configuration analysis."""

from .devices import DeviceBindings
from .diagnostics import Diagnostic
from .ir import Call, ConfigureProperty, DeviceCommand, DeviceIf, If, Literal, Program, StartAgitation, Statement, StopAgitation, While
from .ir.device_contracts import START_AGITATION_ID, STOP_AGITATION_ID
from .ir.traversal import iter_nodes

Configuration = set[tuple[str, str]]


def validate_device_usage(program: Program, bindings: DeviceBindings) -> tuple[Diagnostic, ...]:
    """Check a structurally valid program with complete, compatible bindings.

    Function summaries first compute guaranteed writes, then required incoming
    configuration. Both are monotone fixed points, including recursive graphs;
    the entry is checked with no historical configuration assumptions.
    """
    deployed = {b.logical_id: b for b in bindings.devices}
    resources = {r.node_id: deployed[r.logical_id] for r in program.resources}
    errors = []
    for node, path in iter_nodes(program):
        message = None
        if isinstance(node, DeviceIf):
            message = "Device conditions must be specialized before capability/configuration validation."
        elif isinstance(node, DeviceCommand):
            binding = resources[node.resource_id]
            expected_command = next((c for t in program.device_types for c in t.operations if c.semantic_id == node.operation_id), None)
            actual_command = next((c for c in binding.contract.operations if c.semantic_id == node.operation_id), None)
            if node.operation_id not in binding.supported_operations or expected_command != actual_command:
                message = "The bound device does not implement this command contract."
        elif isinstance(node, ConfigureProperty):
            binding = resources[node.resource_id]
            expected = next((p for c in program.device_types for p in c.properties if p.semantic_id == node.property_id), None)
            actual = next((p for p in binding.contract.properties if p.semantic_id == node.property_id), None)
            if node.property_id not in binding.writable_properties or expected != actual:
                message = "The bound device does not implement this writable property contract."
        elif isinstance(node, (StartAgitation, StopAgitation)):
            operation = START_AGITATION_ID if isinstance(node, StartAgitation) else STOP_AGITATION_ID
            if operation not in resources[node.resource_id].supported_operations:
                message = "The bound device does not support this lifecycle operation."
        if message:
            errors.append(Diagnostic(code="device_capability", message=message, path=path, node_id=node.node_id, source=node.source))
    if errors:
        return tuple(errors)

    guarantees: dict[str, Configuration] = {f.node_id: set() for f in program.functions}
    requirements: dict[str, Configuration] = {f.node_id: set() for f in program.functions}

    def analyze(body: tuple[Statement, ...], available: Configuration) -> tuple[Configuration, Configuration]:
        configured = available.copy()
        required: Configuration = set()
        for statement in body:
            if isinstance(statement, ConfigureProperty):
                configured.add((statement.resource_id, statement.property_id))
            elif isinstance(statement, StartAgitation):
                needs = {(statement.resource_id, p) for p in resources[statement.resource_id].contract.required_configuration}
                required |= needs - configured
            elif isinstance(statement, Call):
                required |= requirements[statement.function_id] - configured
                configured |= guarantees[statement.function_id]
            elif isinstance(statement, If):
                if isinstance(statement.condition, Literal):
                    branch = statement.then_body if statement.condition.value else statement.else_body
                    configured, needs = analyze(branch, configured)
                    required |= needs
                else:
                    left, left_needs = analyze(statement.then_body, configured)
                    right, right_needs = analyze(statement.else_body, configured)
                    configured = left & right
                    required |= left_needs | right_needs
            elif isinstance(statement, While):
                if not (isinstance(statement.condition, Literal) and statement.condition.value is False):
                    _, needs = analyze(statement.body, configured)
                    required |= needs
        return configured, required

    # Guaranteed writes do not depend on preconditions, so solve these first.
    changed = True
    while changed:
        changed = False
        for function in program.functions:
            configured, _ = analyze(function.body, set())
            if configured != guarantees[function.node_id]:
                guarantees[function.node_id] = configured
                changed = True
    changed = True
    while changed:
        changed = False
        for function in program.functions:
            _, required = analyze(function.body, set())
            if required != requirements[function.node_id]:
                requirements[function.node_id] = required
                changed = True
    missing = requirements[program.entry_function_id]
    for resource_id, property_id in sorted(missing):
        node, path = next((n, p) for n, p in iter_nodes(program) if isinstance(n, StartAgitation) and n.resource_id == resource_id)
        errors.append(Diagnostic(
            code="device_configuration", message=f"start() requires {property_id!r} to be configured on every reachable path in this invocation.",
            path=path, node_id=node.node_id, source=node.source,
        ))
    return tuple(errors)
