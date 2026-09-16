"""The typed records own their wire identity, independently of Python names."""

from dataclasses import dataclass
from typing import ClassVar

import pytest

from sciloom.core.diagnostics import IRValidationError
from .model import Program
from .schema import _convert, _record_kinds


@dataclass(frozen=True)
class RenamedRecord:
    __ir_kind__: ClassVar[str] = "OriginalRecord"
    number: int


@dataclass(frozen=True)
class MissingKind:
    number: int


@dataclass(frozen=True)
class InheritedKind(RenamedRecord):
    pass


@dataclass(frozen=True)
class DuplicateKind:
    __ir_kind__: ClassVar[str] = "OriginalRecord"


@dataclass(frozen=True)
class DuplicateDirectory:
    __ir_kind__: ClassVar[str] = "Directory"
    first: RenamedRecord
    second: DuplicateKind


def test_kind_survives_internal_class_rename():
    original = {"kind": "OriginalRecord", "number": 12}
    renamed = _convert(original, RenamedRecord, "$", encode=False)
    assert renamed == RenamedRecord(12)
    assert _convert(renamed, RenamedRecord, "$", encode=True) == original
    # Union selection must also use the wire identity, not the Python class name.
    assert _convert(original, RenamedRecord | None, "$", encode=False) == renamed


@pytest.mark.parametrize("record", [MissingKind, InheritedKind, DuplicateDirectory, RenamedRecord | DuplicateKind])
def test_schema_rejects_missing_inherited_or_duplicate_kinds(record):
    with pytest.raises(IRValidationError) as error:
        _convert(None, record, "$", encode=False)
    assert error.value.diagnostics[0].code == "ir_schema"


def test_program_directory_includes_nested_types_and_source_spans():
    kinds = _record_kinds(Program)
    assert {"SourceSpan", "ListType", "CommandParameter", "InputBinding", "OutputBinding"} <= set(kinds.values())
    assert len(kinds.values()) == len(set(kinds.values()))
    assert all(cls.__dict__["__ir_kind__"] == kind for cls, kind in kinds.items())


def test_unknown_kind_cannot_import_python_objects():
    with pytest.raises(IRValidationError, match="OriginalRecord"):
        _convert({"kind": "os.system", "number": 12}, RenamedRecord | None, "$", encode=False)
