"""Semantic value types and assignment compatibility, independent of source syntax."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar


class ScalarType(StrEnum):
    """Closed semantic scalar vocabulary; quantity values use canonical units."""

    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    TEXT = "text"
    ROTATIONAL_SPEED = "rotational_speed"
    VOLUME = "volume"
    DURATION = "duration"


SIGNED_QUANTITIES = (ScalarType.VOLUME, ScalarType.DURATION)
QUANTITIES = (*SIGNED_QUANTITIES, ScalarType.ROTATIONAL_SPEED)


@dataclass(frozen=True, kw_only=True)
class ListType:
    """One-dimensional homogeneous list type with explicit scalar elements.

    Args:
        element_type: Element type; nested lists and untyped lists are not supported."""

    __ir_kind__: ClassVar[str] = "ListType"

    element_type: ScalarType

    @property
    def value(self) -> str:
        """Return the diagnostic spelling of this semantic list type."""
        return f"list[{self.element_type.value}]"


@dataclass(frozen=True, kw_only=True)
class ZoneType:
    """An ordered set of opaque well references, distinct from scalar and list types."""

    __ir_kind__: ClassVar[str] = "ZoneType"

    @property
    def value(self) -> str:
        """Return the diagnostic spelling of the location value type."""
        return "zone"


ValueType = ScalarType | ListType | ZoneType
"""Scalar, homogeneous scalar list or ordered Zone value type."""


def is_assignable(source: ValueType, target: ValueType) -> bool:
    return source == target or (source == ScalarType.INTEGER and target == ScalarType.REAL)
