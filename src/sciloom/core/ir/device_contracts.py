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
    semantic_id: str
    name: str
    type: ValueType


@dataclass(frozen=True, kw_only=True)
class CommandParameter:
    name: str
    type: ValueType


@dataclass(frozen=True, kw_only=True)
class CommandContract:
    semantic_id: str
    name: str
    parameters: tuple[CommandParameter, ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeviceTypeContract:
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
