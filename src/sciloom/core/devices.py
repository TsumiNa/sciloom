"""Immutable deployment facts without importing Python device implementations."""

from dataclasses import dataclass

from .diagnostics import Diagnostic
from .ir import Program


@dataclass(frozen=True, kw_only=True)
class DeviceBinding:
    logical_id: str
    device_type_id: str
    compatible_type_ids: tuple[str, ...]
    physical_id: str

    def __post_init__(self) -> None:
        for value in (self.logical_id, self.device_type_id, self.physical_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Device binding identities must be nonempty strings.")
        object.__setattr__(self, "compatible_type_ids", tuple(self.compatible_type_ids))
        if any(not isinstance(value, str) or not value for value in self.compatible_type_ids):
            raise ValueError("Compatible device identities must be nonempty strings.")


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
    """Validate the v3 agitation dependency contract against deployment facts."""
    if not isinstance(bindings, DeviceBindings):
        raise TypeError("resolve_devices must return DeviceBindings.")
    provided = {binding.logical_id: binding for binding in bindings.devices}
    required = {resource.logical_id for resource in program.resources}
    errors = []
    for i, resource in enumerate(program.resources):
        binding = provided.get(resource.logical_id)
        code = "missing_resource_binding" if binding is None else "device_type"
        if binding is None or "sciloom.agitator/v1" not in (binding.device_type_id, *binding.compatible_type_ids):
            errors.append(
                Diagnostic(
                    code=code,
                    message=f"No compatible binding for device {resource.logical_id!r}.",
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
