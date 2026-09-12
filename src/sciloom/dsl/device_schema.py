"""Declarative device slots and host-time sharing of logical references."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, get_type_hints

from ..devices.agitation import Agitator
from ..devices.base import BaseDevice


@dataclass(frozen=True, eq=False)
class DeviceReference:
    owner: object
    name: str
    device_type: type[BaseDevice]

    def __getattr__(self, name: str) -> Any:
        raise TypeError("Device operations belong in compiled @runtime methods.")


@dataclass(frozen=True)
class DeviceSlot:
    name: str
    device_type: type[BaseDevice]

    def __get__(self, instance: object | None, owner: type | None = None) -> DeviceReference | DeviceSlot:
        if instance is None:
            return self
        values = vars(instance)
        if self.name not in values:
            values[self.name] = DeviceReference(instance, self.name, self.device_type)
        return values[self.name]

    def __set__(self, instance: object, value: object) -> None:
        if not isinstance(value, DeviceReference) or not issubclass(value.device_type, self.device_type):
            raise TypeError(f"Device slot {self.name!r} requires a compatible logical device reference; bind hardware through Target.")
        vars(instance)[self.name] = value


def build_device_schema(cls: type, reserved: Mapping[str, object]) -> Mapping[str, DeviceSlot]:
    slots: dict[str, DeviceSlot] = {}
    for base in reversed(cls.__mro__[1:]):
        slots.update(getattr(base, "device_fields", {}))
    annotations = get_type_hints(cls, include_extras=True)
    for name in inspect.get_annotations(cls):
        annotation = annotations[name]
        is_device = isinstance(annotation, type) and issubclass(annotation, BaseDevice)
        if name in slots and annotation is not slots[name].device_type:
            raise TypeError(f"Inherited device slot {name!r} cannot change type or field role.")
        if not is_device:
            continue
        if name.startswith("_") or name in reserved or name in getattr(cls, "model_fields", {}):
            raise TypeError(f"Invalid or conflicting device slot name {name!r}.")
        # v3 only carries generic agitation resources. Typed category catalogs
        # become part of the v4 lifecycle contract in the following stage.
        if annotation is not Agitator:
            raise TypeError("JSON v3 supports only Agitator device slots; other device contracts require v4.")
        if name in cls.__dict__ and not isinstance(cls.__dict__[name], DeviceSlot):
            raise TypeError(f"Device slot {name!r} cannot have a class-level value.")
        slots[name] = DeviceSlot(name, annotation)
        setattr(cls, name, slots[name])
    for name, slot in slots.items():
        if inspect.getattr_static(cls, name) is not slot:
            raise TypeError(f"Inherited device slot {name!r} cannot be shadowed.")
    return MappingProxyType(slots)


def component_paths(root: object) -> dict[int, str]:
    """Find stable host composition paths without invoking user descriptors."""
    from .model import Function

    paths = {id(root): ""}
    pending = [root]
    for instance in pending:
        attributes: dict[str, object] = {}
        for cls in reversed(type(instance).__mro__):
            attributes.update(vars(cls))
        attributes.update(vars(instance))
        for name, value in sorted(attributes.items()):
            if isinstance(value, Function) and id(value) not in paths:
                if not name.isidentifier() or name.startswith("_"):
                    raise TypeError("Composed Function names must be public Python identifiers.")
                paths[id(value)] = ".".join(filter(None, (paths[id(instance)], name)))
                pending.append(value)
    return paths
