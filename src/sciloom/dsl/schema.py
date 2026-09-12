"""Runtime field declarations, schema validation and host-access protection."""

from __future__ import annotations

import math
from collections.abc import Container, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Annotated, Any, NoReturn, TypeAlias, TypeVar, get_args, get_origin, get_type_hints
from ..units import RotationalSpeed
from ..core.diagnostics import Diagnostic, IRValidationError
from ..core.ir.types import ListType, ScalarType, ValueType
from ..core.ir import VariableRole


class _FieldRole(Enum):
    INPUT = VariableRole.INPUT
    OUTPUT = VariableRole.OUTPUT
    VAR = VariableRole.INTERNAL


T = TypeVar("T")


Input: TypeAlias = Annotated[T, _FieldRole.INPUT]
Output: TypeAlias = Annotated[T, _FieldRole.OUTPUT]
Var: TypeAlias = Annotated[T, _FieldRole.VAR]


_TYPES = {
    int: ScalarType.INTEGER,
    float: ScalarType.REAL,
    bool: ScalarType.BOOLEAN,
    RotationalSpeed: ScalarType.ROTATIONAL_SPEED,
}


@dataclass(frozen=True, kw_only=True)
class RuntimeField:
    name: str
    role: VariableRole
    type: ValueType
    default: bool | int | float | RotationalSpeed | tuple[bool | int | float | RotationalSpeed, ...] | None = None


def _schema_error(name: str, message: str, code: str = "class_schema") -> NoReturn:
    raise IRValidationError((Diagnostic(code=code, message=message, path=f"$.schema.{name}"),))


class _RuntimeSlot:
    def __init__(self, field: RuntimeField) -> None:
        self.field = field

    def __get__(self, instance: Any, owner: Any = None) -> RuntimeField:
        if instance is not None:
            _schema_error(self.field.name, "Runtime fields cannot be read by host Python.", "runtime_field_read")
        return self.field

    def __set__(self, instance: Any, value: Any) -> None:
        _schema_error(
            self.field.name,
            "Declare defaults on the class; runtime writes belong in @runtime methods.",
            "runtime_field_write",
        )


def build_schema(cls: type, reserved_names: Container[str]) -> Mapping[str, RuntimeField]:
    inherited: dict[str, RuntimeField] = {}
    for base in reversed(cls.__mro__[1:]):
        inherited.update(getattr(base, "model_fields", {}))
    try:
        annotations = get_type_hints(cls, include_extras=True)
    except (NameError, TypeError) as error:
        _schema_error(cls.__name__, f"Cannot resolve class annotations: {error}")
    registered = inherited.copy()
    for name, annotation in annotations.items():
        arguments = get_args(annotation) if get_origin(annotation) is Annotated else ()
        roles = [item for item in arguments[1:] if isinstance(item, _FieldRole)]
        if not roles:
            if name in inherited or _contains_role(annotation):
                _schema_error(name, "Runtime fields require one direct Input[T], Output[T] or Var[T] role.")
            continue
        if len(roles) != 1:
            _schema_error(name, "Runtime fields require exactly one role; nested roles are unsupported.")
        value_type = _value_type(name, arguments[0])
        if name in reserved_names or name.startswith("_"):
            _schema_error(name, "Runtime field name conflicts with the model API.")
        role = roles[0].value
        if name in inherited and name not in cls.__dict__:
            default = inherited[name].default
        else:
            default = cls.__dict__.get(name)
            if role == VariableRole.INTERNAL:
                default = _default(name, default, value_type)
        if role != VariableRole.INTERNAL and name in cls.__dict__:
            _schema_error(name, "Parameter defaults are outside the first frontend subset.")
        field = RuntimeField(name=name, role=role, type=value_type, default=default)
        if name in inherited and field != inherited[name]:
            _schema_error(
                name, "Overriding runtime schema is unsupported; specialize host-time configuration instead."
            )
        registered[name] = field
    for name, field in registered.items():
        setattr(cls, name, _RuntimeSlot(field))
    return MappingProxyType(registered)


def _contains_role(annotation: Any) -> bool:
    """Reject roles hidden inside other typing constructs instead of treating them as host fields."""
    if isinstance(annotation, _FieldRole):
        return True
    return any(_contains_role(argument) for argument in get_args(annotation))


def _value_type(name: str, annotation: Any) -> ValueType:
    if get_origin(annotation) is list:
        args = get_args(annotation)
        if len(args) != 1 or not isinstance(args[0], type) or args[0] not in _TYPES:
            _schema_error(name, "Lists require one supported scalar element type; Any and nested lists are unsupported.")
        return ListType(element_type=_TYPES[args[0]])
    if not isinstance(annotation, type) or annotation not in _TYPES:
        _schema_error(name, "Input, Output and Var require int, float, bool, RotationalSpeed or a typed list of those values.")
    return _TYPES[annotation]


def _default(name: str, value: Any, value_type: ValueType) -> Any:
    if isinstance(value_type, ListType):
        if type(value) is not list:
            _schema_error(name, "Var requires an explicit list initial value.")
        return tuple(_default(name, item, value_type.element_type) for item in value)
    if value is None:
        _schema_error(name, "Var requires an explicit scalar literal initial value.")
    allowed = {
        ScalarType.INTEGER: (int,), ScalarType.REAL: (int, float),
        ScalarType.BOOLEAN: (bool,), ScalarType.ROTATIONAL_SPEED: (RotationalSpeed,),
    }[value_type]
    if type(value) not in allowed or (type(value) is float and not math.isfinite(value)):
        _schema_error(name, f"Default must be a finite {value_type.value} value.")
    return value
