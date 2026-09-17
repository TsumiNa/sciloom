"""Serializable device interfaces; semantic identifiers never import Python code."""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from .types import ListType, ScalarType, ValueType

DEVICE_TYPE_ID = "sciloom.device/v1"
AGITATOR_TYPE_ID = "sciloom.agitator/v1"
AGITATION_SPEED_ID = "sciloom.agitator.speed/v1"
START_AGITATION_ID = "sciloom.agitator.start/v1"
STOP_AGITATION_ID = "sciloom.agitator.stop/v1"
HEATER_TYPE_ID = "sciloom.heater/v1"
HEATER_TEMPERATURE_ID = "sciloom.heater.temperature/v1"
HEATER_RAMP_RATE_ID = "sciloom.heater.ramp-rate/v1"
START_HEATER_ID = "sciloom.heater.start/v1"
STOP_HEATER_ID = "sciloom.heater.stop/v1"


@dataclass(frozen=True, kw_only=True)
class PropertyContract:
    """Configuration identity and scalar/list value type; locations are not capabilities."""

    __ir_kind__: ClassVar[str] = "PropertyContract"

    semantic_id: str
    name: str
    type: ScalarType | ListType


@dataclass(frozen=True, kw_only=True)
class CommandParameter:
    """Typed scalar, homogeneous list or Zone argument of a no-return command."""

    __ir_kind__: ClassVar[str] = "CommandParameter"

    name: str
    type: ValueType


@dataclass(frozen=True, kw_only=True)
class CommandContract:
    """Serializable command signature; no executable Python object is stored."""

    __ir_kind__: ClassVar[str] = "CommandContract"

    semantic_id: str
    name: str
    parameters: tuple[CommandParameter, ...] = ()


class LifecycleEffect(StrEnum):
    """Defined logical effects, independent of command names and hardware success."""

    APPLY_AND_ENABLE = "apply_and_enable"
    DISABLE = "disable"


@dataclass(frozen=True, kw_only=True)
class LifecycleCommandContract:
    """Explicit parameterless command effect and required property semantic IDs.

    Applying also requires the concrete device's required configuration. Disabling
    has only its explicit requirements and retains saved and applied snapshots.
    The parameters field must be empty for the two currently defined effects.
    """

    __ir_kind__: ClassVar[str] = "LifecycleCommandContract"

    semantic_id: str
    name: str
    effect: LifecycleEffect
    parameters: tuple[CommandParameter, ...] = ()
    required_configuration: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeviceTypeContract:
    """Versioned device interface and its required configuration.

    Attributes:
        type_id: Namespaced, versioned semantic identity.
        base_type_ids: Complete ancestor identities.
        properties: Declared configuration signatures, including inherited members.
        operations: Declared no-return command signatures.
        required_configuration: Property semantic IDs required before startup."""

    __ir_kind__: ClassVar[str] = "DeviceTypeContract"

    type_id: str
    base_type_ids: tuple[str, ...] = ()
    properties: tuple[PropertyContract, ...] = ()
    operations: tuple[CommandContract | LifecycleCommandContract, ...] = ()
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

HEATER_CONTRACT = DeviceTypeContract(
    type_id=HEATER_TYPE_ID,
    base_type_ids=(DEVICE_TYPE_ID,),
    properties=(
        PropertyContract(semantic_id=HEATER_TEMPERATURE_ID, name="temperature", type=ScalarType.TEMPERATURE),
        PropertyContract(semantic_id=HEATER_RAMP_RATE_ID, name="ramp_rate", type=ScalarType.TEMPERATURE_RATE),
    ),
    operations=(
        LifecycleCommandContract(
            semantic_id=START_HEATER_ID,
            name="start",
            effect=LifecycleEffect.APPLY_AND_ENABLE,
            required_configuration=(HEATER_TEMPERATURE_ID, HEATER_RAMP_RATE_ID),
        ),
        LifecycleCommandContract(semantic_id=STOP_HEATER_ID, name="stop", effect=LifecycleEffect.DISABLE),
    ),
    required_configuration=(HEATER_TEMPERATURE_ID, HEATER_RAMP_RATE_ID),
)
