"""Structural schema shared by typed validation and JSON conversion."""

import math
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from functools import cache
from types import UnionType
from typing import Any, ClassVar, NoReturn, get_args, get_origin, get_type_hints

from sciloom.core.diagnostics import Diagnostic, IRValidationError


def _fail(code: str, message: str, path: str) -> NoReturn:
    raise IRValidationError((Diagnostic(code=code, message=message, path=path),))


@cache
def _field_types(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


@cache
def _record_kinds(expected: Any) -> dict[type, str]:
    """Derive the closed wire vocabulary from typed fields, never module scanning.

    Inspect the complete reachable schema, even records absent from one value.
    Own declarations prevent a subclass from accidentally reusing a base kind.
    No wire identifier can select a Python type outside this schema.
    """
    records: dict[type, str] = {}
    owners: dict[str, type] = {}

    def visit(annotation: Any) -> None:
        if isinstance(annotation, type) and is_dataclass(annotation):
            if annotation in records:
                return
            kind = annotation.__dict__.get("__ir_kind__")
            hints = _field_types(annotation)
            if type(kind) is not str or not kind.strip() or hints.get("__ir_kind__") != ClassVar[str]:
                _fail("ir_schema", f"{annotation.__name__} must declare its own __ir_kind__: ClassVar[str].", "$")
            if kind in owners:
                _fail(
                    "ir_schema",
                    f"Duplicate IR kind {kind!r}: {owners[kind].__name__} and {annotation.__name__}.",
                    "$",
                )
            owners[kind] = annotation
            records[annotation] = kind
            for field in fields(annotation):
                visit(hints[field.name])
        else:
            for argument in get_args(annotation):
                visit(argument)

    visit(expected)
    return records


def _convert(value: Any, expected: Any, path: str, *, encode: bool) -> Any:
    """Validate structure while converting; both directions share one schema."""
    kinds = _record_kinds(expected)
    code = "ir_shape" if encode else "json_shape"
    origin = get_origin(expected)
    if origin is UnionType:
        choices = get_args(expected)
        for choice in choices:
            if isinstance(choice, type) and is_dataclass(choice):
                matches = (
                    type(value) is choice
                    if encode
                    else (isinstance(value, dict) and value.get("kind") == kinds[choice])
                )
            elif isinstance(choice, type) and issubclass(choice, Enum):
                matches = type(value) is choice if encode else type(value) is str
            else:
                matches = type(value) is choice
            if matches:
                return _convert(value, choice, path, encode=encode)
        _fail(code, f"Expected one of: {', '.join(kinds.get(c, c.__name__) for c in choices)}.", path)

    if origin is tuple:
        if type(value) is not (tuple if encode else list):
            _fail(code, "Expected a tuple." if encode else "Expected an array.", path)
        items = [_convert(item, get_args(expected)[0], f"{path}[{i}]", encode=encode) for i, item in enumerate(value)]
        return items if encode else tuple(items)

    if isinstance(expected, type) and is_dataclass(expected):
        kind = kinds[expected]
        if encode:
            if type(value) is not expected:
                _fail(code, f"Expected {expected.__name__}.", path)
            raw = {f.name: getattr(value, f.name) for f in fields(expected)}
        else:
            if not isinstance(value, dict) or value.get("kind") != kind:
                _fail(code, f"Expected an object with kind={kind!r}.", path)
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
        return {"kind": kind, **converted} if encode else expected(**converted)

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
