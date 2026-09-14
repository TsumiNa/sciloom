"""Immutable deployment facts without importing Python device implementations."""

from dataclasses import dataclass

from .diagnostics import Diagnostic
from .ir import Program
from .ir.device_contracts import DeviceTypeContract
from .ir.device_validation import semantic_id, validate_directory
from .ir.schema import _convert


@dataclass(frozen=True, kw_only=True)
class DeviceBinding:
    """Trusted deployment facts for one logical device.

    Attributes:
        logical_id: Declared field/component path.
        contract: Concrete device's trusted data contract.
        base_contracts: Complete trusted ancestor directory.
        physical_id: Target-defined unique hardware identity.
        writable_properties: Supported property semantic IDs.
        supported_operations: Supported command semantic IDs.

    Raises:
        TypeError: The concrete contract is not a DeviceTypeContract.
        IRValidationError: Concrete or ancestor contract fields have invalid shapes.
        ValueError: Identities, ancestry or capability declarations are inconsistent."""

    logical_id: str
    contract: DeviceTypeContract
    base_contracts: tuple[DeviceTypeContract, ...]
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
        object.__setattr__(self, "base_contracts", tuple(self.base_contracts))
        _convert(self.base_contracts, tuple[DeviceTypeContract, ...], "$.binding.base_contracts", encode=True)
        if {c.type_id for c in self.base_contracts} != set(self.contract.base_type_ids):
            raise ValueError("base_contracts must provide the complete trusted ancestor directory.")
        contract_errors: list[str] = []
        validate_directory(
            Program(entry_function_id="", device_types=(*self.base_contracts, self.contract)),
            lambda code, message, path, node: contract_errors.append(message),
        )
        if contract_errors:
            raise ValueError("Invalid trusted device directory: " + "; ".join(contract_errors))
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
    """Immutable, conflict-checked collection of trusted device bindings.

    Args:
        devices: Bindings with unique logical and physical identities.

    Raises:
        TypeError: An entry is not a DeviceBinding.
        ValueError: Identities or trusted contract definitions conflict."""

    devices: tuple[DeviceBinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "devices", tuple(self.devices))
        if any(not isinstance(value, DeviceBinding) for value in self.devices):
            raise TypeError("DeviceBindings requires DeviceBinding records.")
        contracts: dict[str, DeviceTypeContract] = {}
        for binding in self.devices:
            for contract in (*binding.base_contracts, binding.contract):
                if contracts.setdefault(contract.type_id, contract) != contract:
                    raise ValueError("Conflicting trusted device contracts across bindings.")
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
        if binding is None or resource.device_type_id not in (
            binding.contract.type_id,
            *binding.contract.base_type_ids,
        ):
            errors.append(
                Diagnostic(
                    code=code,
                    message=f"No compatible binding for device {resource.logical_id!r}.",
                    path=f"$.resources[{i}]",
                    node_id=resource.node_id,
                    source=resource.source,
                )
            )
        elif any(
            c.type_id == trusted.type_id and c != trusted
            for c in program.device_types
            for trusted in (*binding.base_contracts, binding.contract)
        ):
            errors.append(
                Diagnostic(
                    code="device_contract",
                    message="Serialized device contract differs from the target's trusted contract.",
                    path=f"$.resources[{i}]",
                    node_id=resource.node_id,
                    source=resource.source,
                )
            )
    for name in sorted(provided.keys() - required):
        errors.append(
            Diagnostic(
                code="unknown_resource_binding",
                message=f"Device binding {name!r} has no declared resource.",
                path="$.resources",
            )
        )
    return tuple(errors)
