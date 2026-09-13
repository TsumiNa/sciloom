"""Serializable device interfaces; semantic identifiers never import Python code."""

from dataclasses import dataclass

from .types import ScalarType, ValueType

DEVICE_TYPE_ID = "sciloom.device/v1"
AGITATOR_TYPE_ID = "sciloom.agitator/v1"
AGITATION_SPEED_ID = "sciloom.agitator.speed/v1"
START_AGITATION_ID = "sciloom.agitator.start/v1"
STOP_AGITATION_ID = "sciloom.agitator.stop/v1"


@dataclass(frozen=True, kw_only=True)
class PropertyContract:
    """Serializable configuration property identity, user-facing name and value type."""

    semantic_id: str
    name: str
    type: ValueType


@dataclass(frozen=True, kw_only=True)
class CommandParameter:
    """Named, typed argument of a no-return device command."""

    name: str
    type: ValueType


@dataclass(frozen=True, kw_only=True)
class CommandContract:
    """Serializable command signature; no executable Python object is stored."""

    semantic_id: str
    name: str
    parameters: tuple[CommandParameter, ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeviceTypeContract:
    """Versioned device interface and its required configuration.

    Attributes:
        type_id: Namespaced, versioned semantic identity.
        base_type_ids: Complete ancestor identities.
        properties: Declared configuration signatures, including inherited members.
        operations: Declared no-return command signatures.
        required_configuration: Property semantic IDs required before startup."""

    type_id: str
    base_type_ids: tuple[str, ...] = ()
    properties: tuple[PropertyContract, ...] = ()
    operations: tuple[CommandContract, ...] = ()
    required_configuration: tuple[str, ...] = ()


BASE_DEVICE_CONTRACT = DeviceTypeContract(type_id=DEVICE_TYPE_ID)
AGITATOR_CONTRACT = DeviceTypeContract(
    type_id=AGITATOR_TYPE_ID,
    base_type_ids=(DEVICE_TYPE_ID,),
    properties=(PropertyContract(semantic_id=AGITATION_SPEED_ID, name="speed", type=ScalarType.ROTATIONAL_SPEED),),
    operations=(
        CommandContract(semantic_id=START_AGITATION_ID, name="start"),
        CommandContract(semantic_id=STOP_AGITATION_ID, name="stop"),
    ),
    required_configuration=(AGITATION_SPEED_ID,),
)
