"""Immutable deployment facts without importing Python device implementations."""

from dataclasses import dataclass

from .diagnostics import Diagnostic
from .ir import Program
from .ir.device_contracts import DeviceTypeContract
from .ir.device_validation import semantic_id
from .ir.schema import _convert


@dataclass(frozen=True, kw_only=True)
class DeviceBinding:
    logical_id: str
    contract: DeviceTypeContract
    physical_id: str
    writable_properties: tuple[str, ...] = ()
    supported_operations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.logical_id, self.physical_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Device binding identities must be nonempty strings.")
        if not isinstance(self.contract, DeviceTypeContract):
            raise TypeError("DeviceBinding requires a trusted DeviceTypeContract.")
        _convert(self.contract, DeviceTypeContract, "$.binding.contract", encode=True)
        if any(not semantic_id(value) for value in (self.contract.type_id, *self.contract.base_type_ids)):
            raise ValueError("Device type identities must be namespaced and versioned.")
        for name, available in (
            ("writable_properties", {p.semantic_id for p in self.contract.properties}),
            ("supported_operations", {op.semantic_id for op in self.contract.operations}),
        ):
            values = tuple(getattr(self, name))
            object.__setattr__(self, name, values)
            if len(values) != len(set(values)) or not set(values) <= available:
                raise ValueError(f"{name} must identify distinct declared device members.")
        if not set(self.contract.required_configuration) <= set(self.writable_properties):
            raise ValueError("Required device configuration must be writable.")


@dataclass(frozen=True, kw_only=True)
class DeviceBindings:
    devices: tuple[DeviceBinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "devices", tuple(self.devices))
        if any(not isinstance(value, DeviceBinding) for value in self.devices):
            raise TypeError("DeviceBindings requires DeviceBinding records.")
        for field in ("logical_id", "physical_id"):
            values = [getattr(value, field) for value in self.devices]
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate device binding {field}.")


def validate_bindings(program: Program, bindings: DeviceBindings) -> tuple[Diagnostic, ...]:
    """Validate typed dependencies and selected deployment identity facts."""
    if not isinstance(bindings, DeviceBindings):
        raise TypeError("resolve_devices must return DeviceBindings.")
    provided = {binding.logical_id: binding for binding in bindings.devices}
    required = {resource.logical_id for resource in program.resources}
    errors = []
    for i, resource in enumerate(program.resources):
        binding = provided.get(resource.logical_id)
        code = "missing_resource_binding" if binding is None else "device_type"
        if binding is None or resource.device_type_id not in (binding.contract.type_id, *binding.contract.base_type_ids):
            errors.append(
                Diagnostic(
                    code=code,
                    message=f"No compatible binding for device {resource.logical_id!r}.",
                    path=f"$.resources[{i}]",
                    node_id=resource.node_id,
                    source=resource.source,
                )
            )
        elif any(c.type_id == binding.contract.type_id and c != binding.contract for c in program.device_types):
            errors.append(Diagnostic(code="device_contract", message="Serialized device contract differs from the target's trusted contract.", path=f"$.resources[{i}]", node_id=resource.node_id, source=resource.source))
    for name in sorted(provided.keys() - required):
        errors.append(
            Diagnostic(
                code="unknown_resource_binding",
                message=f"Device binding {name!r} has no declared resource.",
                path="$.resources",
            )
        )
    return tuple(errors)
