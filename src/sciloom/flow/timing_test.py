"""Wall-time vocabulary retains a typed signature without reading the host clock."""

from inspect import signature

import pytest

from sciloom import now_text as public_now_text
from .timing import now_text


def test_now_text_is_host_protected_and_retains_signature():
    assert public_now_text is now_text
    contract = signature(now_text)
    assert tuple(contract.parameters) == ("format",)
    assert contract.return_annotation is str
    assert contract.bind("%Y").arguments == contract.bind(format="%Y").arguments
    with pytest.raises(TypeError, match="compiled @runtime"):
        now_text("%Y")
