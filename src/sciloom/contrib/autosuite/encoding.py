"""Encode AutoSuite scalar types and variable initialization records."""

from __future__ import annotations

from dataclasses import dataclass
from ...core.ir import ScalarType, Variable
from .xml import XmlNode, xml_node as _xml


@dataclass(frozen=True)
class ScalarEncoding:
    parameter_type: str
    storage_type: str
    si_unit: str
    display_unit: str


SCALARS = {
    ScalarType.INTEGER: ScalarEncoding("integer", "3", "1", "s"),
    ScalarType.REAL: ScalarEncoding("realnumber", "5", "1", "1"),
    ScalarType.BOOLEAN: ScalarEncoding("bool", "11", "1", "s"),
    ScalarType.ROTATIONAL_SPEED: ScalarEncoding("angularspeed", "5", "1/s", "rpm"),
}


def number(value: bool | int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def variable_declaration(variable: Variable, name: str) -> XmlNode:
    assert variable.initial is not None  # guaranteed by shared validation
    value = (
        ("-1" if variable.initial.value else "0")
        if variable.type == ScalarType.BOOLEAN
        else number(variable.initial.value)
    )
    return (
        _xml(
            "variable",
            "",
            _xml("name", name),
            _xml("value", "", _xml("type", SCALARS[variable.type].storage_type), _xml("value", value)),
            _xml("siunit", SCALARS[variable.type].si_unit),
            _xml("unit", SCALARS[variable.type].display_unit),
            _xml("array", "0"),
            _xml("creationtime", "0"),
            _xml("constant", "0"),
        )
    )
