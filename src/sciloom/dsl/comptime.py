"""Typed device predicates recognized only in compiled if/elif conditions."""

from typing import Callable, TypeGuard, TypeVar

from ..devices import BaseDevice

T = TypeVar("T", bound=BaseDevice)


def can_write(device: BaseDevice, name: str) -> bool:
    """Query an explicitly declared writable capability of the bound device."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")


def supports(device: BaseDevice, command: Callable[..., None]) -> bool:
    """Query a registered command, independently of Python inheritance."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")


def is_device(device: BaseDevice, device_type: type[T]) -> TypeGuard[T]:
    """Narrow the declared interface when the binding is this type or a subtype."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")
