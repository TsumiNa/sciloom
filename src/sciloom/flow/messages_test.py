"""The public notification marker is host-protected and has no return value."""

from inspect import signature

import pytest

from sciloom import notify as public_notify
from .messages import notify


def test_host_protection_and_public_signature():
    assert public_notify is notify
    contract = signature(notify)
    assert tuple(contract.parameters) == ("message",)
    assert contract.return_annotation is None
    assert contract.bind("Ready?").arguments == contract.bind(message="Ready?").arguments
    with pytest.raises(TypeError, match="compiled @runtime"):
        notify("Ready?")
