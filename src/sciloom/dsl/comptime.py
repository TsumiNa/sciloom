"""Typed device predicates recognized only in compiled if/elif conditions."""

from typing import Callable, TypeGuard, TypeVar

from ..devices import BaseDevice

T = TypeVar("T", bound=BaseDevice)


def can_write(device: BaseDevice, name: str) -> bool:
    """Query the bound device's explicit writable capability.
    
    Args:
        device: Logical device slot inside a runtime method.
        name: String literal naming a declared property.
    
    Returns:
        A compile-time Boolean used only in an if/elif condition.
    
    Raises:
        TypeError: Called directly by host Python.
    
    This query does not narrow the Python device type."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")


def supports(device: BaseDevice, command: Callable[..., None]) -> bool:
    """Query a registered command independently of Python inheritance.
    
    Args:
        device: Logical device slot inside a runtime method.
        command: Registered command method, for example `Agitator.start`.
    
    Returns:
        A compile-time Boolean used only in an if/elif condition.
    
    Raises:
        TypeError: Called directly by host Python."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")


def is_device(device: BaseDevice, device_type: type[T]) -> TypeGuard[T]:
    """Narrow a logical interface to a bound device type or subtype.
    
    Args:
        device: Logical device slot inside a runtime method.
        device_type: Declared device class with a versioned semantic identity.
    
    Returns:
        A type guard recognized by type checkers and compiled if/elif conditions.
    
    Raises:
        TypeError: Called directly by host Python.
    
    The IR retains both branches until specialization with trusted bindings."""
    raise TypeError("comptime queries belong in compiled if/elif conditions.")
