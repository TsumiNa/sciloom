"""Function-owned timer declarations, independent of device bindings and values."""

import inspect
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, get_type_hints

from .fields import _schema_error
from .timing import Timer


@dataclass(frozen=True)
class TimerSlot:
    name: str

    def __get__(self, instance: object | None, owner: type | None = None) -> "TimerSlot":
        if instance is not None:
            raise TypeError("Timer slots are only accessible in compiled @runtime methods.")
        return self

    def __set__(self, instance: object, value: object) -> None:
        raise TypeError("Timers are Function-owned declarations; assignment and sharing are unsupported.")


def build_timer_schema(cls: type, reserved: Mapping[str, object]) -> Mapping[str, TimerSlot]:
    slots: dict[str, TimerSlot] = {}
    for base in reversed(cls.__mro__[1:]):
        slots.update(getattr(base, "timer_fields", {}))
    annotations = get_type_hints(cls, include_extras=True)
    for name in inspect.get_annotations(cls):
        annotation = annotations[name]
        if name in slots and annotation is not Timer:
            _schema_error(name, "Inherited timer slots cannot change type or field role.")
        if isinstance(annotation, type) and issubclass(annotation, Timer) and annotation is not Timer:
            _schema_error(name, "Timer subclasses are unsupported; declare a bare Timer.")
        if annotation is not Timer:
            continue
        if name.startswith("_") or name in reserved or name in getattr(cls, "model_fields", {}):
            _schema_error(name, "Invalid or conflicting timer slot name.")
        if name in cls.__dict__ and not isinstance(cls.__dict__[name], TimerSlot):
            _schema_error(name, "Timer slots cannot have class-level values.")
        for base in cls.__mro__[1:]:
            member = base.__dict__.get(name)
            if (name in base.__dict__ and not isinstance(member, TimerSlot)) or (
                name in inspect.get_annotations(base) and name not in getattr(base, "timer_fields", {})
            ):
                _schema_error(name, "Timer slots cannot replace inherited host, device or runtime fields.")
        slots[name] = TimerSlot(name)
        setattr(cls, name, slots[name])
    for name, slot in slots.items():
        if inspect.getattr_static(cls, name) is not slot:
            _schema_error(name, "Inherited timer slots cannot be shadowed.")
    return MappingProxyType(slots)
