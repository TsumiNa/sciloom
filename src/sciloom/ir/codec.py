"""Strict, versioned JSON interchange using the model's declared field types.

The closed dataclass unions define the allowed node kinds. No JSON value is
imported as a Python class, evaluated as code or coerced to a different scalar.
"""

import json
import math
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from functools import cache
from types import UnionType
from typing import Any, NoReturn, cast, get_args, get_origin, get_type_hints

from ..diagnostics import Diagnostic, IRValidationError
from .model import Package


def _fail(code: str, message: str, path: str) -> NoReturn:
    raise IRValidationError((Diagnostic(code=code, message=message, path=path),))


@cache
def _field_types(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


def _convert(value: Any, expected: Any, path: str, *, encode: bool) -> Any:
    """Validate structure while converting; both directions share one schema."""
    code = "ir_shape" if encode else "json_shape"
    origin = get_origin(expected)
    if origin is UnionType:
        choices = get_args(expected)
        for choice in choices:
            if isinstance(choice, type) and is_dataclass(choice):
                matches = (
                    type(value) is choice
                    if encode
                    else (isinstance(value, dict) and value.get("kind") == choice.__name__)
                )
            else:
                matches = type(value) is choice
            if matches:
                return _convert(value, choice, path, encode=encode)
        _fail(code, f"Expected one of: {', '.join(c.__name__ for c in choices)}.", path)

    if origin is tuple:
        if type(value) is not (tuple if encode else list):
            _fail(code, "Expected a tuple." if encode else "Expected an array.", path)
        items = [_convert(item, get_args(expected)[0], f"{path}[{i}]", encode=encode) for i, item in enumerate(value)]
        return items if encode else tuple(items)

    if isinstance(expected, type) and is_dataclass(expected):
        if encode:
            if type(value) is not expected:
                _fail(code, f"Expected {expected.__name__}.", path)
            raw = {f.name: getattr(value, f.name) for f in fields(expected)}
        else:
            if not isinstance(value, dict) or value.get("kind") != expected.__name__:
                _fail(code, f"Expected an object with kind={expected.__name__!r}.", path)
            unknown = set(value) - {f.name for f in fields(expected)} - {"kind"}
            if unknown:
                _fail(code, f"Unknown fields: {', '.join(sorted(map(str, unknown)))}.", path)
            raw = value
        converted = {}
        for f in fields(expected):
            if f.name not in raw:
                if f.default is not MISSING or f.default_factory is not MISSING:
                    continue
                _fail(code, f"Missing required field {f.name!r}.", f"{path}.{f.name}")
            converted[f.name] = _convert(raw[f.name], _field_types(expected)[f.name], f"{path}.{f.name}", encode=encode)
        return {"kind": expected.__name__, **converted} if encode else expected(**converted)

    if isinstance(expected, type) and issubclass(expected, Enum):
        if encode:
            if type(value) is not expected:
                _fail(code, f"Expected {expected.__name__} enum.", path)
            return value.value
        if type(value) is not str:
            _fail(code, f"Expected a {expected.__name__} string.", path)
        try:
            return expected(value)
        except ValueError:
            _fail(code, f"Unknown {expected.__name__} value {value!r}.", path)

    if type(value) is not expected:
        _fail(code, f"Expected {expected.__name__}.", path)
    if type(value) is float and not math.isfinite(value):
        _fail(code, "Numbers must be finite.", path)
    return value


def to_dict(package: Package) -> dict[str, Any]:
    """Validate a package and return a detached JSON-compatible object."""
    from .validation import validate

    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return cast(dict[str, Any], _convert(package, Package, "$", encode=True))


def from_dict(document: dict[str, Any]) -> Package:
    """Construct typed IR, rejecting malformed or semantically invalid documents."""
    from .validation import validate

    if not isinstance(document, dict) or "format_version" not in document:
        _fail("json_shape", "A package must declare format_version.", "$.format_version")
    try:
        package = cast(Package, _convert(document, Package, "$", encode=False))
    except RecursionError:
        _fail("json_shape", "Document is cyclic or nested too deeply.", "$")
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    return package


def to_json(package: Package) -> str:
    """Produce deterministic, readable JSON; retain IDs and semantic list order."""
    return json.dumps(to_dict(package), ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"


def from_json(text: str) -> Package:
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
