"""Static property/command declarations shared by device categories and contributors."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Callable, NoReturn, ParamSpec, get_args, get_origin, get_type_hints

from sciloom.core.bindings import DeviceBinding
from sciloom.core.diagnostics import Diagnostic, IRValidationError
from sciloom.core.ir.device_contracts import CommandContract, CommandParameter, DeviceTypeContract, PropertyContract
from sciloom.core.ir.device_validation import semantic_id
from sciloom.core.ir.types import ListType, ScalarType, ValueType
from sciloom.units import Duration, RotationalSpeed, Volume
from .base import BaseDevice

P = ParamSpec("P")


def _declaration_error(subject: str, message: str) -> NoReturn:
    raise IRValidationError((Diagnostic(code="device_contract", message=message, path=f"$.device.{subject}"),))


def operation(*, id: str) -> Callable[[Callable[P, None]], Callable[P, None]]:
    """Register a setter or no-return command, preserving its Python signature.

    Args:
        id: Stable namespaced and versioned semantic identity.

    Returns:
        A decorator that registers the method and blocks host execution.

    Raises:
        IRValidationError: The semantic ID is malformed.
        TypeError: The decorated operation is called by host Python.
    """
    if not semantic_id(id):
        _declaration_error(id, "Operation IDs must be namespaced and versioned.")

    def decorate(method: Callable[P, None]) -> Callable[P, None]:
        @wraps(method)
        def guarded(*args: P.args, **kwargs: P.kwargs) -> None:
            raise TypeError("Device operations belong in compiled @runtime methods.")

        setattr(guarded, "__sciloom_operation_id__", id)
        return guarded

    return decorate


def value_type(annotation: object) -> ValueType:
    """Device values use the same native scalar and homogeneous list vocabulary."""
    scalars = {
        int: ScalarType.INTEGER,
        float: ScalarType.REAL,
        bool: ScalarType.BOOLEAN,
        str: ScalarType.TEXT,
        RotationalSpeed: ScalarType.ROTATIONAL_SPEED,
        Volume: ScalarType.VOLUME,
        Duration: ScalarType.DURATION,
    }
    if isinstance(annotation, type) and annotation in scalars:
        return scalars[annotation]
    if get_origin(annotation) is list:
        args = get_args(annotation)
        if len(args) == 1 and isinstance(args[0], type) and args[0] in scalars:
            return ListType(element_type=scalars[args[0]])
    _declaration_error("value", "Device values require a supported scalar, quantity or homogeneous scalar list type.")


def device_contract(cls: type[BaseDevice]) -> DeviceTypeContract:
    """Read descriptors and signatures without executing device method bodies.

    Args:
        cls: Device category or concrete profile with its own semantic type ID.

    Returns:
        A serializable contract containing inherited declarations and ancestry.

    Raises:
        IRValidationError: A type identity, property or command declaration is invalid.
    """
    type_id = cls.__dict__.get("device_type_id")
    if not isinstance(type_id, str) or not semantic_id(type_id):
        _declaration_error(cls.__name__, "Each device class requires its own versioned device_type_id.")
    properties = []
    commands = []
    members: dict[str, object] = {}
    for base in reversed(cls.__mro__):
        members.update(vars(base))
    for name, member in members.items():
        method = member.fset if isinstance(member, property) else member
        semantic = inspect.getattr_static(method, "__sciloom_operation_id__", None)
        if semantic is None:
            continue
        if not callable(method):
            _declaration_error(name, "Registered operations must be methods or property setters.")
        hints = get_type_hints(method)
        parameters = list(inspect.signature(method).parameters.values())
        if hints.get("return") is not type(None) or not parameters:
            _declaration_error(name, "Device operations must declare a receiver and return None.")
        if parameters[0].kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            _declaration_error(name, "Device operations require an ordinary instance receiver.")
        arguments = []
        for parameter in parameters[1:]:
            if parameter.default is not inspect.Parameter.empty or parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                _declaration_error(name, "Device commands do not support defaults or variadic arguments.")
            arguments.append(CommandParameter(name=parameter.name, type=value_type(hints.get(parameter.name))))
        if isinstance(member, property):
            if len(arguments) != 1 or member.fget is None or len(inspect.signature(member.fget).parameters) != 1:
                _declaration_error(name, "Device setters require one typed value and a matching getter declaration.")
            if parameters[1].kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                _declaration_error(name, "Device setters require a positional value parameter.")
            getter_type = value_type(get_type_hints(member.fget).get("return"))
            if getter_type != arguments[0].type:
                _declaration_error(name, "Device getter and setter types must match.")
            properties.append(PropertyContract(semantic_id=semantic, name=name, type=getter_type))
        else:
            commands.append(CommandContract(semantic_id=semantic, name=name, parameters=tuple(arguments)))
    by_name = {p.name: p.semantic_id for p in properties}
    required = inspect.getattr_static(cls, "required_configuration", ())
    if not isinstance(required, tuple) or any(name not in by_name for name in required):
        _declaration_error(cls.__name__, "required_configuration must list declared property names.")
    return DeviceTypeContract(
        type_id=type_id,
        base_type_ids=tuple(base.device_type_id for base in cls.__mro__[1:] if issubclass(base, BaseDevice)),
        properties=tuple(properties),
        operations=tuple(commands),
        required_configuration=tuple(by_name[name] for name in required),
    )


def bind_device(*, logical_id: str, device: BaseDevice, physical_id: str) -> DeviceBinding:
    """Translate an explicit concrete profile into contributor-neutral facts.

    Args:
        logical_id: Declared logical device field/component path.
        device: Concrete profile explicitly declaring its supported capabilities.
        physical_id: Target-defined hardware identity, unique across bindings.

    Returns:
        An immutable binding with the complete trusted ancestor directory.

    Raises:
        TypeError: The profile omits a capability list or names an undeclared member.
        IRValidationError: The profile's own or an ancestor's contract is invalid.
        ValueError: The resulting binding violates trusted-contract invariants.
    """
    cls = type(device)
    for name in ("writable_properties", "required_configuration", "supported_operations"):
        if name not in cls.__dict__:
            raise TypeError(f"Concrete device profiles must explicitly declare {name}.")
    contract = device_contract(cls)
    properties = {p.name: p.semantic_id for p in contract.properties}
    writable = cls.__dict__["writable_properties"]
    operations = cls.__dict__["supported_operations"]
    if not isinstance(writable, tuple) or any(name not in properties for name in writable):
        raise TypeError("writable_properties must list declared property names.")
    if not isinstance(operations, tuple) or any(not callable(method) for method in operations):
        raise TypeError("supported_operations must list registered command methods.")
    return DeviceBinding(
        logical_id=logical_id,
        contract=contract,
        physical_id=physical_id,
        base_contracts=tuple(device_contract(base) for base in cls.__mro__[1:] if issubclass(base, BaseDevice)),
        writable_properties=tuple(properties[name] for name in writable),
        supported_operations=tuple(getattr(method, "__sciloom_operation_id__", "") for method in operations),
    )
