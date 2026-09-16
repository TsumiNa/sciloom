"""Independent snapshots of saved configuration, applied values and lifecycle."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import assert_never

from sciloom.core.bindings import DeviceBinding, DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.ir import ConfigureProperty, DeviceAt, DeviceResource, Program, StartAgitation, StopAgitation
from sciloom.core.ir.device_contracts import START_AGITATION_ID, STOP_AGITATION_ID
from sciloom.core.locations import LocationDirectory, Zone
from .values import OutputValue, RuntimeValue, coerce, fail, output_value


@dataclass(frozen=True, kw_only=True)
class DeviceState:
    """Separate saved configuration, last-applied configuration and enabled state.

    Attributes:
        configuration: Captured property values keyed by property name.
        applied_configuration: Complete configuration last applied by start.
        enabled: Lifecycle result of the logical resource's last start/stop.
            With runtime selection, inspect physical_devices for every controller.

    Stopping preserves both mappings. Configuration writes do not change applied values."""

    configuration: Mapping[str, OutputValue] = field(default_factory=dict)
    applied_configuration: Mapping[str, OutputValue] = field(default_factory=dict)
    enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))
        object.__setattr__(self, "applied_configuration", MappingProxyType(dict(self.applied_configuration)))


@dataclass(frozen=True, kw_only=True)
class PhysicalDeviceState:
    """Applied configuration and lifecycle of one physical controller.

    Logical configuration writes do not change this snapshot. A start applies
    the logical resource's saved values; a stop retains these applied values.
    """

    applied_configuration: Mapping[str, OutputValue] = field(default_factory=dict)
    enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "applied_configuration", MappingProxyType(dict(self.applied_configuration)))


@dataclass(frozen=True, kw_only=True)
class DeviceEvent:
    """Device operation occurrence and its resulting immutable state snapshot."""

    node_id: str
    resource_id: str
    operation_id: str
    state: DeviceState
    physical_id: str | None = None
    physical_state: PhysicalDeviceState | None = None


class DeviceSession:
    def __init__(self, program: Program, bindings: DeviceBindings | None = None) -> None:
        devices = tuple(r for r in program.resources if isinstance(r, DeviceResource))
        supplied = {} if bindings is None else {binding.logical_id: binding for binding in bindings.devices}
        self.bindings = {r.node_id: supplied[r.logical_id] for r in devices if r.logical_id in supplied}
        self.active: dict[str, tuple[Zone, DeviceCandidate]] = {}
        self.physical: dict[str, PhysicalDeviceState] = {}
        for binding in self.bindings.values():
            identities = (
                (binding.physical_id,)
                if isinstance(binding, DeviceBinding)
                else tuple(candidate.binding.physical_id for candidate in binding.candidates)
            )
            self.physical.update((identity, PhysicalDeviceState()) for identity in identities)
        self.states = {r.node_id: DeviceState() for r in devices}
        self.contracts = {
            r.node_id: (
                self.bindings[r.node_id].contract
                if r.node_id in self.bindings
                else next(c for c in program.device_types if c.type_id == r.device_type_id)
            )
            for r in devices
        }
        self.properties = {
            p.semantic_id: p for c in (*program.device_types, *self.contracts.values()) for p in c.properties
        }

    def select(self, node: DeviceAt, zone: Zone, directory: LocationDirectory) -> None:
        """Validate a captured selection completely before installing its context."""
        binding = self.bindings.get(node.resource_id)
        if binding is None:
            fail("missing_environment_service", "Device location scopes require explicit device_bindings.", node)
        if not isinstance(binding, DeviceSelectionBinding):
            fail("device_selection_binding", "at() requires an explicit candidate selection binding.", node)
        if node.resource_id in self.active:
            fail("device_selection_nesting", "The same logical device is already selected.", node)
        if not zone.well_ids:
            fail("device_location", "An empty Zone cannot select a physical controller.", node)
        known = {well.identity for well in directory.wells}
        selected = set(zone.well_ids)
        if not selected <= known:
            fail("unknown_well", "The location includes an identity absent from the reference directory.", node)
        matches = [candidate for candidate in binding.candidates if selected <= set(candidate.wells.well_ids)]
        if len(matches) != 1:
            fail(
                "device_location", "The location must lie wholly within one candidate controller's allowed wells.", node
            )
        self.active[node.resource_id] = (zone, matches[0])

    def apply(
        self, statement: ConfigureProperty | StartAgitation | StopAgitation, value: RuntimeValue | None = None
    ) -> DeviceEvent:
        previous = self.states[statement.resource_id]
        binding = self.bindings.get(statement.resource_id)
        physical_id = binding.physical_id if isinstance(binding, DeviceBinding) else None
        if isinstance(binding, DeviceSelectionBinding):
            selected = self.active.get(statement.resource_id)
            if selected is not None:
                physical_id = selected[1].binding.physical_id
            elif not isinstance(statement, ConfigureProperty):
                fail("device_selection_required", "A physical command requires an active at() scope.", statement)
        if isinstance(statement, ConfigureProperty):
            if binding is not None and statement.property_id not in binding.writable_properties:
                fail("device_capability", "This configuration property is not supported by the deployment.", statement)
            assert value is not None
            prop = self.properties[statement.property_id]
            saved = output_value(coerce(value, prop.type, statement), prop.type)
            state = replace(previous, configuration={**previous.configuration, prop.name: saved})
            operation = prop.semantic_id
        elif isinstance(statement, StartAgitation):
            if binding is not None and START_AGITATION_ID not in binding.supported_operations:
                fail("device_capability", "The deployment does not support agitation start.", statement)
            required = {self.properties[p].name for p in self.contracts[statement.resource_id].required_configuration}
            if not required <= previous.configuration.keys():
                fail("device_configuration", "start() requires complete saved configuration.", statement)
            state = replace(previous, applied_configuration=previous.configuration, enabled=True)
            operation = START_AGITATION_ID
            if physical_id is not None:
                self.physical[physical_id] = PhysicalDeviceState(
                    applied_configuration=state.configuration, enabled=True
                )
        elif isinstance(statement, StopAgitation):
            if binding is not None and STOP_AGITATION_ID not in binding.supported_operations:
                fail("device_capability", "The deployment does not support agitation stop.", statement)
            state = replace(previous, enabled=False)
            operation = STOP_AGITATION_ID
            if physical_id is not None:
                self.physical[physical_id] = replace(self.physical[physical_id], enabled=False)
        else:
            assert_never(statement)
        self.states[statement.resource_id] = state
        return DeviceEvent(
            node_id=statement.node_id,
            resource_id=statement.resource_id,
            operation_id=operation,
            state=state,
            physical_id=physical_id,
            physical_state=self.physical.get(physical_id) if physical_id is not None else None,
        )
