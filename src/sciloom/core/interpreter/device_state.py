"""Independent snapshots of saved configuration, applied values and lifecycle."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from ..ir import ConfigureProperty, Program, StartAgitation, StopAgitation
from ..ir.device_contracts import START_AGITATION_ID, STOP_AGITATION_ID
from .values import OutputValue, RuntimeValue, coerce, fail, output_value


@dataclass(frozen=True, kw_only=True)
class DeviceState:
    configuration: Mapping[str, OutputValue] = field(default_factory=dict)
    applied_configuration: Mapping[str, OutputValue] = field(default_factory=dict)
    enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))
        object.__setattr__(self, "applied_configuration", MappingProxyType(dict(self.applied_configuration)))


@dataclass(frozen=True, kw_only=True)
class DeviceEvent:
    node_id: str
    resource_id: str
    operation_id: str
    state: DeviceState


class DeviceSession:
    def __init__(self, program: Program) -> None:
        self.states = {r.node_id: DeviceState() for r in program.resources}
        self.contracts = {r.node_id: next(c for c in program.device_types if c.type_id == r.device_type_id) for r in program.resources}
        self.properties = {p.semantic_id: p for c in program.device_types for p in c.properties}

    def apply(self, statement: ConfigureProperty | StartAgitation | StopAgitation, value: RuntimeValue | None = None) -> DeviceEvent:
        previous = self.states[statement.resource_id]
        if isinstance(statement, ConfigureProperty):
            assert value is not None
            prop = self.properties[statement.property_id]
            saved = output_value(coerce(value, prop.type, statement), prop.type)
            state = replace(previous, configuration={**previous.configuration, prop.name: saved})
            operation = prop.semantic_id
        elif isinstance(statement, StartAgitation):
            required = {self.properties[p].name for p in self.contracts[statement.resource_id].required_configuration}
            if not required <= previous.configuration.keys():
                fail("device_configuration", "start() requires complete saved configuration.", statement)
            state = replace(previous, applied_configuration=previous.configuration, enabled=True)
            operation = START_AGITATION_ID
        else:
            state = replace(previous, enabled=False)
            operation = STOP_AGITATION_ID
        self.states[statement.resource_id] = state
        return DeviceEvent(node_id=statement.node_id, resource_id=statement.resource_id, operation_id=operation, state=state)
