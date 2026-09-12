"""Strict, versioned JSON interchange for the typed semantic model."""

import json
from typing import Any, cast

from ..diagnostics import IRValidationError
from .model import Program
from .schema import _convert, _fail
from .validation import validate


def to_dict(package: Program) -> dict[str, Any]:
    """Validate a package and return a detached JSON-compatible object."""
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return cast(dict[str, Any], _convert(package, Program, "$", encode=True))


def from_dict(document: dict[str, Any]) -> Program:
    """Construct typed IR, rejecting malformed or semantically invalid documents."""
    if not isinstance(document, dict) or "format_version" not in document:
        _fail("json_shape", "A package must declare format_version.", "$.format_version")
    try:
        package = cast(Program, _convert(document, Program, "$", encode=False))
    except RecursionError:
        _fail("json_shape", "Document is cyclic or nested too deeply.", "$")
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return package


def to_json(package: Program) -> str:
    """Produce deterministic, readable JSON; retain IDs and semantic list order."""
    return json.dumps(to_dict(package), ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"


def from_json(text: str) -> Program:
    """Parse JSON without duplicate keys or nonstandard NaN/Infinity values."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                _fail("json_syntax", f"Duplicate object key {key!r}.", "$")
            result[key] = value
        return result

    def constant(value: str) -> None:
        _fail("json_syntax", f"Nonstandard JSON constant {value!r}.", "$")

    try:
        document = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as error:
        if isinstance(error, IRValidationError):
            raise
        _fail("json_syntax", f"Invalid JSON: {error}", "$")
    return from_dict(document)
