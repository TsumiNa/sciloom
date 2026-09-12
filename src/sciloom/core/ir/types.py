"""Semantic value types and assignment compatibility, independent of source syntax."""

from __future__ import annotations

from enum import StrEnum
from dataclasses import dataclass


class ScalarType(StrEnum):
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    ROTATIONAL_SPEED = "rotational_speed"


@dataclass(frozen=True, kw_only=True)
class ListType:
    element_type: ScalarType

    @property
    def value(self) -> str:
        return f"list[{self.element_type.value}]"


ValueType = ScalarType | ListType


def is_assignable(source: ValueType, target: ValueType) -> bool:
    return source == target or (source == ScalarType.INTEGER and target == ScalarType.REAL)
