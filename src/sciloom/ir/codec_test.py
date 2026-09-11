"""JSON is an interchange boundary, not a bypass around IR validation."""

import json
from dataclasses import replace

import pytest

from sciloom.ir import (
    IRValidationError,
    SourceSpan,
    from_dict,
    from_json,
    to_dict,
    to_json,
    validate,
)


def test_round_trip_preserves_semantics_ids_and_source(package):
    function = replace(package.functions[0], source=SourceSpan(path="example.py", line=10, column=4))
    package = replace(package, functions=(function, package.functions[1]))
    encoded = to_json(package)
    assert from_json(encoded) == package
    assert to_json(from_dict(to_dict(package))) == encoded
    assert validate(package) == ()


@pytest.mark.parametrize(
    "mutate,code",
    [
        (lambda d: d.update(format_version=1), "format_version"),
        (lambda d: d.pop("format_version"), "json_shape"),
        (lambda d: d.update(format_version=True), "json_shape"),
        (lambda d: d.update(unknown=True), "json_shape"),
        (lambda d: d.update(entry_function_id="missing"), "entry_function"),
        (lambda d: d["functions"][0].update(kind="ApplicationIR"), "json_shape"),
        (lambda d: d["functions"][0]["variables"][0].update(type="volume"), "json_shape"),
        (lambda d: d["functions"][0].pop("node_id"), "json_shape"),
        (lambda d: d["functions"][0]["body"][0]["value"].update(symbol_id="missing"), "unknown_symbol"),
    ],
)
def test_invalid_documents_have_diagnostics(package, mutate, code):
    document = to_dict(package)
    mutate(document)
    with pytest.raises(IRValidationError) as error:
        from_dict(document)
    assert code in {d.code for d in error.value.diagnostics}
    assert all(d.path.startswith("$") for d in error.value.diagnostics)


@pytest.mark.parametrize("text", ["{", "null", "[]", '{"kind":"Program","kind":"Program"}', '{"x":NaN}'])
def test_malformed_json_fails_explicitly(text):
    with pytest.raises(IRValidationError):
        from_json(text)


def test_nonfinite_real_is_not_interchangeable(package):
    document = to_dict(package)
    document["functions"][1]["variables"][0]["initial"]["value"] = float("inf")
    with pytest.raises(IRValidationError):
        from_dict(document)


def test_export_validates_too(package):
    with pytest.raises(IRValidationError) as error:
        to_json(replace(package, entry_function_id="unknown"))
    assert error.value.diagnostics[0].code == "entry_function"


def test_bad_typed_construction_is_a_diagnostic(package):
    broken = replace(package, functions="not a tuple")
    assert validate(broken)[0].code == "ir_shape"


def test_ids_are_required_not_generated_on_import(package):
    document = json.loads(to_json(package))
    document["functions"][0]["node_id"] = ""
    with pytest.raises(IRValidationError) as error:
        from_dict(document)
    assert "empty_id" in {d.code for d in error.value.diagnostics}
