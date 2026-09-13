"""Semantic value types and assignment compatibility, independent of source syntax."""

from __future__ import annotations

from enum import StrEnum
from dataclasses import dataclass


class ScalarType(StrEnum):
    """Closed semantic scalar vocabulary; quantity values use canonical units."""
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    ROTATIONAL_SPEED = "rotational_speed"


@dataclass(frozen=True, kw_only=True)
class ListType:
    """One-dimensional homogeneous list type with explicit scalar elements.

    Args:
        element_type: Element type; nested lists and untyped lists are not supported."""
    element_type: ScalarType

    @property
    def value(self) -> str:
        """Return the diagnostic spelling of this semantic list type."""
        return f"list[{self.element_type.value}]"


ValueType = ScalarType | ListType
"""Scalar or one-dimensional homogeneous list value type."""


def is_assignable(source: ValueType, target: ValueType) -> bool:
    return source == target or (source == ScalarType.INTEGER and target == ScalarType.REAL)
