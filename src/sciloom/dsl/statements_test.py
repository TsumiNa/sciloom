"""Source diagnostics describe author syntax, not lowering implementation details."""

import pytest

from sciloom import Function, runtime
from sciloom.core.diagnostics import IRValidationError


def test_unsupported_call_describes_supported_self_syntax():
    class UnsupportedCall(Function):
        @runtime
        def run(self):
            print(1)

    with pytest.raises(IRValidationError) as caught:
        UnsupportedCall().to_ir()
    diagnostic = caught.value.diagnostics[0]
    assert diagnostic.code == "python_subset"
    assert "self.<function>" in diagnostic.message
    assert "context" not in diagnostic.message
    assert diagnostic.source is not None
    assert diagnostic.source.path.endswith("statements_test.py")
