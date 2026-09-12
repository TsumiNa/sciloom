"""Semantic value types and assignment compatibility, independent of source syntax."""

from __future__ import annotations

from enum import StrEnum


class ScalarType(StrEnum):
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    ROTATIONAL_SPEED = "rotational_speed"


def is_assignable(source: ScalarType, target: ScalarType) -> bool:
    return source == target or (source == ScalarType.INTEGER and target == ScalarType.REAL)
