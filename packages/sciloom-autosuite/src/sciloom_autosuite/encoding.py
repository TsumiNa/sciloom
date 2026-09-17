"""Encode AutoSuite scalar types and variable initialization records."""

from __future__ import annotations

from dataclasses import dataclass

from sciloom.core.diagnostics import CompilationError, Diagnostic
from sciloom.core.ir import ListLiteral, ListType, Literal, ScalarType, ValueType, Variable, ZoneLiteral, ZoneType
from sciloom.core.ir.types import THERMAL_QUANTITIES
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
    ScalarType.TEXT: ScalarEncoding("text", "8", "text", "K/s"),
    ScalarType.ROTATIONAL_SPEED: ScalarEncoding("angularspeed", "5", "1/s", "rpm"),
    ScalarType.VOLUME: ScalarEncoding("volume", "5", "m^3", "ml"),
    ScalarType.DURATION: ScalarEncoding("time", "5", "s", "s"),
}

ZONE = ScalarEncoding("zone", "8", "zone", "zone")


def value_encoding(value_type: ValueType) -> ScalarEncoding:
    """Select an observed vendor encoding without treating Zones as list elements."""
    if isinstance(value_type, ZoneType):
        return ZONE
    if isinstance(value_type, ListType):
        value_type = value_type.element_type
    if value_type in THERMAL_QUANTITIES:
        raise CompilationError(
            (
                Diagnostic(
                    code="unsupported_temperature_type", message="AutoSuite thermal encoding is not verified.", path="$"
                ),
            )
        )
    if value_type in (ScalarType.FLOW_RATE, ScalarType.LENGTH):
        raise CompilationError(
            (
                Diagnostic(
                    code="unsupported_transfer_quantity",
                    message="AutoSuite flow/length encoding is not verified.",
                    path="$",
                ),
            )
        )
    return SCALARS[value_type]


def number(value: bool | int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def literal_value(literal: Literal, *, storage: bool = False) -> str:
    """Encode an expression literal; XML escaping is handled by the XML writer.

    Text uses quoted runs and documented Char codes instead of assuming an
    undocumented backslash/apostrophe escape convention in the expression parser.
    """
    value = literal.value
    if literal.type in (*THERMAL_QUANTITIES, ScalarType.FLOW_RATE, ScalarType.LENGTH):
        value_encoding(literal.type)  # Explicitly reject direct backend calls, too.
    if literal.type == ScalarType.TEXT:
        assert isinstance(value, str)
        parts: list[str] = []
        run = ""
        for character in value:
            code = ord(character)
            if code == 0 or 0xD800 <= code <= 0xDFFF or code in (0xFFFE, 0xFFFF):
                raise CompilationError(
                    (
                        Diagnostic(
                            code="unsupported_text_literal",
                            message="AutoSuite text literals cannot contain NUL or invalid XML characters.",
                            path="$",
                            node_id=literal.node_id,
                            source=literal.source,
                        ),
                    )
                )
            if code < 32 or character in "'\\":
                if run:
                    parts.append("'" + run + "'")
                    run = ""
                parts.append(f"Char({code})")
            else:
                run += character
        if run:
            parts.append("'" + run + "'")
        if not parts:
            return "''"
        return parts[0] if len(parts) == 1 else "(" + " + ".join(parts) + ")"
    assert not isinstance(value, str)
    if literal.type == ScalarType.BOOLEAN:
        return ("-1" if value else "0") if storage else ("true" if value else "false")
    return number(value)


def variable_declaration(variable: Variable, name: str) -> XmlNode:
    assert variable.initial is not None  # guaranteed by shared validation
    if isinstance(variable.type, ListType):
        assert isinstance(variable.initial, ListLiteral)
        encoding = value_encoding(variable.type)
        values = []
        for i, element in enumerate(variable.initial.elements):
            assert isinstance(element, Literal)
            text = literal_value(element, storage=True)
            values.append(_xml(f"value{i}", "", _xml("type", encoding.storage_type), _xml("value", text)))
        return _xml(
            "variable",
            "",
            _xml("name", name),
            _xml("values", "", _xml("count", str(len(values))), *values),
            _xml("type", encoding.storage_type),
            _xml("siunit", encoding.si_unit),
            _xml("unit", "1" if variable.type.element_type == ScalarType.INTEGER else encoding.display_unit),
            _xml("array", "1"),
            _xml("creationtime", "0"),
            _xml("constant", "0"),
        )
    encoding = value_encoding(variable.type)
    if isinstance(variable.type, ZoneType):
        assert isinstance(variable.initial, ZoneLiteral)
        if variable.initial.well_ids:
            raise CompilationError(
                (
                    Diagnostic(
                        code="unsupported_zone_literal",
                        message="AutoSuite supports only empty Zone initializers; resolve named Zones at runtime.",
                        path="$",
                        node_id=variable.node_id,
                        source=variable.source,
                    ),
                )
            )
        value = ""
    else:
        assert isinstance(variable.initial, Literal)
        value = literal_value(variable.initial, storage=True)
    return _xml(
        "variable",
        "",
        _xml("name", name),
        _xml("value", "", _xml("type", encoding.storage_type), _xml("value", value)),
        _xml("siunit", encoding.si_unit),
        _xml("unit", encoding.display_unit),
        _xml("array", "0"),
        _xml("creationtime", "0"),
        _xml("constant", "0"),
    )
