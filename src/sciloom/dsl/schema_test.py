"""Runtime defaults are validated when the class schema is built."""

import pytest

from sciloom import Boolean, Function, Integer, Real
from sciloom.core.diagnostics import IRValidationError


@pytest.mark.parametrize(
    "scalar,value",
    [
        (Integer, True),
        (Integer, 1.5),
        (Real, False),
        (Boolean, 1),
        (Real, float("nan")),
        (Real, float("inf")),
    ],
)
def test_internal_default_type_is_checked_before_instantiation(scalar, value):
    with pytest.raises(IRValidationError, match="class_schema") as error:

        class Bad(Function):
            field: scalar = value

    assert error.value.diagnostics[0].path == "$.schema.field"


def test_real_default_allows_integer_widening():
    class Allowed(Function):
        field: Real = 0

    assert Allowed.model_fields["field"].default == 0
