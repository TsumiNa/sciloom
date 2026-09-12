"""Runtime defaults are validated when the class schema is built."""

import pytest
from typing import Annotated, Any, ClassVar, get_args, get_type_hints

from sciloom import Function, Input, Output, RotationalSpeed, Var, rpm
from sciloom.core.diagnostics import IRValidationError


@pytest.mark.parametrize(
    "scalar,value",
    [
        (int, True),
        (int, 1.5),
        (float, False),
        (bool, 1),
        (float, float("nan")),
        (float, float("inf")),
    ],
)
def test_internal_default_type_is_checked_before_instantiation(scalar, value):
    with pytest.raises(IRValidationError, match="class_schema") as error:

        class Bad(Function):
            field: Var[scalar] = value

    assert error.value.diagnostics[0].path == "$.schema.field"


def test_real_default_allows_integer_widening():
    class Allowed(Function):
        field: Var[float] = 0

    assert Allowed.model_fields["field"].default == 0


def test_native_roles_preserve_types_metadata_and_host_configuration():
    class Fields(Function):
        source: Input[float]
        result: Output[bool]
        index: Var[int] = 0
        speed: Var[RotationalSpeed] = 600 * rpm
        batch_size: int = 8
        coefficient: float = 2.0
        host_speed: RotationalSpeed = 10 * rpm

    assert set(Fields.model_fields) == {"source", "result", "index", "speed"}
    assert get_type_hints(Fields)["source"] is float
    assert get_args(get_type_hints(Fields, include_extras=True)["index"])[0] is int
    instance = Fields()
    instance.batch_size = 12
    assert instance.batch_size == 12
    assert instance.coefficient == 2.0
    assert instance.host_speed == 10 * rpm
    for name in Fields.model_fields:
        with pytest.raises(IRValidationError, match="runtime_field_read"):
            getattr(instance, name)
        with pytest.raises(IRValidationError, match="runtime_field_write"):
            setattr(instance, name, 1)


@pytest.mark.parametrize("annotation", [
    Input, Output, Var, Input[Any], Var[list], Var[list[int]],
    Var[Input[float]], Output[Var[int]], Input[Input[float]],
    ClassVar[Input[int]],
])
def test_invalid_role_or_type_is_a_schema_error(annotation):
    with pytest.raises(IRValidationError, match="class_schema"):
        type("Invalid", (Function,), {"__annotations__": {"value": annotation}, "value": 0})


@pytest.mark.parametrize("attributes", [{}, {"value": None}])
def test_var_requires_an_explicit_valid_initial_value(attributes):
    with pytest.raises(IRValidationError, match="Var requires"):
        type("MissingDefault", (Function,), {"__annotations__": {"value": Var[int]}, **attributes})


def test_single_role_allows_unrelated_annotated_metadata():
    class Described(Function):
        value: Annotated[Var[int], "counter"] = 0

    assert Described.model_fields["value"].default == 0


def test_inherited_role_and_default_cannot_be_changed():
    class Base(Function):
        value: Var[int] = 0

    class Child(Base):
        option: int = 2

    assert Child.model_fields == Base.model_fields
    for annotation, default in [(int, 0), (Var[float], 0), (Var[int], 1), (Input[int], 0)]:
        with pytest.raises(IRValidationError, match="class_schema"):
            type("Changed", (Base,), {"__annotations__": {"value": annotation}, "value": default})


def test_legacy_type_markers_are_removed_from_the_author_api():
    import sciloom

    for name in ("Real", "Integer", "Boolean"):
        assert not hasattr(sciloom, name)
