"""The public log marker is runtime-only and requires named category/stream."""

from inspect import Parameter, signature

import pytest

from sciloom import log as public_log
from .logging import log


def test_host_call_guard():
    with pytest.raises(TypeError, match="compiled @runtime"):
        log(1, category="recipe", stream="count")


def test_public_export_and_signature():
    assert public_log is log
    contract = signature(public_log)
    assert tuple(contract.parameters) == ("value", "category", "stream")
    assert contract.parameters["category"].kind == Parameter.KEYWORD_ONLY
    assert contract.parameters["stream"].kind == Parameter.KEYWORD_ONLY
    assert contract.return_annotation is None
    assert contract.bind(1, category="recipe", stream="count").arguments == {
        "value": 1,
        "category": "recipe",
        "stream": "count",
    }
    with pytest.raises(TypeError):
        contract.bind(1, "recipe", "count")
    with pytest.raises(TypeError):
        contract.bind(1, category="recipe")
