"""Immutable deployment facts without importing Python device implementations."""

from dataclasses import dataclass

from .diagnostics import Diagnostic
from .ir import DeviceResource, Program
from .ir.device_contracts import DeviceTypeContract
from .ir.device_validation import semantic_id, validate_directory
from .ir.schema import _convert
from .locations import Zone


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
class DeviceCandidate:
    """One trusted physical controller and its nonempty allowed well selection.

    Args:
        binding: Existing single-controller deployment facts.
        wells: Opaque identities allowed for this candidate, not display names.

    Raises:
        TypeError: Either value is not its declared immutable record type.
        ValueError: No wells are allowed.
    """

    binding: DeviceBinding
    wells: Zone

    def __post_init__(self) -> None:
        if not isinstance(self.binding, DeviceBinding) or type(self.wells) is not Zone:
            raise TypeError("DeviceCandidate requires a DeviceBinding and a Zone.")
        if not self.wells.well_ids:
            raise ValueError("A device candidate requires nonempty allowed wells.")


@dataclass(frozen=True, kw_only=True)
class DeviceSelectionBinding:
    """Bounded runtime choice among controllers with one common trusted contract.

    Args:
        logical_id: Declared logical resource shared by all candidates.
        candidates: Nonempty, copied tuple of distinct physical candidates.

    Raises:
        TypeError: A candidate is not a DeviceCandidate.
        ValueError: Logical IDs, contracts or capabilities differ, or physical
            identities/allowed well sets overlap.

    There is no physical_id on this record: selection happens during execution.
    """

    logical_id: str
    candidates: tuple[DeviceCandidate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidates", tuple(self.candidates))
        if any(type(candidate) is not DeviceCandidate for candidate in self.candidates):
            raise TypeError("Selection bindings require DeviceCandidate records.")
        if not self.candidates:
            raise ValueError("Selection bindings require at least one candidate.")
        first = self.candidates[0].binding
        physical: set[str] = set()
        wells: set[str] = set()
        for candidate in self.candidates:
            binding = candidate.binding
            if binding.logical_id != self.logical_id:
                raise ValueError("Every candidate must bind the selection's logical_id.")
            if (
                binding.contract != first.contract
                or {c.type_id: c for c in binding.base_contracts} != {c.type_id: c for c in first.base_contracts}
                or set(binding.writable_properties) != set(first.writable_properties)
                or set(binding.supported_operations) != set(first.supported_operations)
            ):
                raise ValueError("Selection candidates must have identical trusted contracts and capabilities.")
            if binding.physical_id in physical or wells.intersection(candidate.wells.well_ids):
                raise ValueError("Selection candidates must have distinct controllers and disjoint wells.")
            physical.add(binding.physical_id)
            wells.update(candidate.wells.well_ids)

    @property
    def contract(self) -> DeviceTypeContract:
        """Common concrete type contract, independent of the runtime selection."""
        return self.candidates[0].binding.contract

    @property
    def base_contracts(self) -> tuple[DeviceTypeContract, ...]:
        """Common complete ancestor directory."""
        return self.candidates[0].binding.base_contracts

    @property
    def writable_properties(self) -> tuple[str, ...]:
        """Properties supported by every candidate."""
        return self.candidates[0].binding.writable_properties

    @property
    def supported_operations(self) -> tuple[str, ...]:
        """Commands supported by every candidate."""
        return self.candidates[0].binding.supported_operations


@dataclass(frozen=True, kw_only=True)
class DeviceBindings:
    """Immutable, conflict-checked collection of trusted device bindings.

    Args:
        devices: Fixed/selection bindings with unique logical and physical identities.

    Raises:
        TypeError: An entry is not a DeviceBinding or DeviceSelectionBinding.
        ValueError: Identities or trusted contract definitions conflict."""

    devices: tuple[DeviceBinding | DeviceSelectionBinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "devices", tuple(self.devices))
        if any(not isinstance(value, (DeviceBinding, DeviceSelectionBinding)) for value in self.devices):
            raise TypeError("DeviceBindings requires DeviceBinding or DeviceSelectionBinding records.")
        contracts: dict[str, DeviceTypeContract] = {}
        for binding in self.devices:
            for contract in (*binding.base_contracts, binding.contract):
                if contracts.setdefault(contract.type_id, contract) != contract:
                    raise ValueError("Conflicting trusted device contracts across bindings.")
        logical = [value.logical_id for value in self.devices]
        if len(logical) != len(set(logical)):
            raise ValueError("Duplicate device binding logical_id.")
        physical: set[str] = set()
        wells: set[str] = set()
        for value in self.devices:
            identities = (
                (value.physical_id,)
                if isinstance(value, DeviceBinding)
                else tuple(candidate.binding.physical_id for candidate in value.candidates)
            )
            if physical.intersection(identities):
                raise ValueError("Duplicate device binding physical_id.")
            physical.update(identities)
            if isinstance(value, DeviceSelectionBinding):
                selected = {well for candidate in value.candidates for well in candidate.wells.well_ids}
                if wells.intersection(selected):
                    raise ValueError("Different logical resources cannot share candidate wells.")
                wells.update(selected)


def validate_bindings(program: Program, bindings: DeviceBindings) -> tuple[Diagnostic, ...]:
    """Validate typed dependencies and selected deployment identity facts."""
    if not isinstance(bindings, DeviceBindings):
        raise TypeError("resolve_devices must return DeviceBindings.")
    provided = {binding.logical_id: binding for binding in bindings.devices}
    required = {resource.logical_id for resource in program.resources if isinstance(resource, DeviceResource)}
    errors = []
    for i, resource in enumerate(program.resources):
        if not isinstance(resource, DeviceResource):
            continue
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
