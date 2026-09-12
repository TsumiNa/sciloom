"""Runtime field declarations, schema validation and host-access protection."""

from __future__ import annotations

import math
from collections.abc import Container, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, NoReturn, TypeVar, get_args, get_origin, get_type_hints
from ..units import RotationalSpeed
from ..core.diagnostics import Diagnostic, IRValidationError
from ..core.ir.types import ScalarType
from ..core.ir import VariableRole


class Integer:
    """SciLoom integer runtime type (not Python int)."""


class Real:
    """SciLoom real runtime type (not Python float)."""


class Boolean:
    """SciLoom boolean runtime type (not Python bool)."""


T = TypeVar("T")


class Input(Generic[T]):
    """Typed function input declaration."""


class Output(Generic[T]):
    """Typed function output declaration."""


_TYPES = {
    Integer: ScalarType.INTEGER,
    Real: ScalarType.REAL,
    Boolean: ScalarType.BOOLEAN,
    RotationalSpeed: ScalarType.ROTATIONAL_SPEED,
}


@dataclass(frozen=True, kw_only=True)
class RuntimeField:
    name: str
    role: VariableRole
    type: ScalarType
    default: bool | int | float | RotationalSpeed | None = None


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
        annotations = get_type_hints(cls)
    except (NameError, TypeError) as error:
        _schema_error(cls.__name__, f"Cannot resolve class annotations: {error}")
    registered = inherited.copy()
    for name, annotation in annotations.items():
        if annotation in (Input, Output):
            _schema_error(name, "Input and Output require an explicit scalar type argument.")
        origin = get_origin(annotation)
        is_parameter = origin in (Input, Output)
        scalar = get_args(annotation)[0] if is_parameter else annotation
        if scalar not in _TYPES:
            if is_parameter or name in inherited:
                _schema_error(name, "Runtime fields require Integer, Real, Boolean or RotationalSpeed.")
            continue
        if name in reserved_names or name.startswith("_"):
            _schema_error(name, "Runtime field name conflicts with the model API.")
        role = (
            VariableRole.INPUT
            if origin is Input
            else VariableRole.OUTPUT
            if origin is Output
            else VariableRole.INTERNAL
        )
        if name in inherited and name not in cls.__dict__:
            default = inherited[name].default
        else:
            default = cls.__dict__.get(name)
        if role == VariableRole.INTERNAL and type(default) not in (bool, int, float, RotationalSpeed):
            _schema_error(name, "Internal variables require a scalar literal default.")
        if role == VariableRole.INTERNAL:
            allowed_types = {
                Integer: (int,),
                Real: (int, float),
                Boolean: (bool,),
                RotationalSpeed: (RotationalSpeed,),
            }[scalar]
            if type(default) not in allowed_types or (type(default) is float and not math.isfinite(default)):
                _schema_error(name, f"Default must be a finite {scalar.__name__} value.")
        if role != VariableRole.INTERNAL and name in cls.__dict__:
            _schema_error(name, "Parameter defaults are outside the first frontend subset.")
        field = RuntimeField(name=name, role=role, type=_TYPES[scalar], default=default)
        if name in inherited and field != inherited[name]:
            _schema_error(
                name, "Overriding runtime schema is unsupported; specialize host-time configuration instead."
            )
        registered[name] = field
    for name, field in registered.items():
        setattr(cls, name, _RuntimeSlot(field))
    return MappingProxyType(registered)
