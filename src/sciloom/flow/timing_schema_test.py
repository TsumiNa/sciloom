"""Timer declarations stay separate from values and cannot be shared or shadowed."""

import pytest

from sciloom import Agitator, Function, Timer, Var, runtime, s, wait
from sciloom.core.diagnostics import IRValidationError


class Timed(Function):
    timer: Timer

    @runtime
    def run(self) -> None:
        self.timer.start()
        wait(2 * s)
        self.timer.wait_until(duration=5 * s)


def test_timer_schema_inheritance_and_host_protection():
    class Inherited(Timed):
        pass

    assert tuple(Inherited.timer_fields) == ("timer",)
    assert not Inherited.model_fields and not Inherited.device_fields
    assert Inherited().to_ir().resources[0].owner_id == "fn:0"
    for operation in (lambda: Timer(), lambda: Timed().timer, lambda: wait(1 * s)):
        with pytest.raises(TypeError):
            operation()
    with pytest.raises(TypeError):
        Timed().timer = object()


def test_conflicting_timer_declarations_are_schema_errors():
    with pytest.raises(IRValidationError):

        class Changed(Timed):
            timer: Var[int] = 0

    with pytest.raises(IRValidationError):

        class Device(Timed):
            timer: Agitator

    with pytest.raises(IRValidationError):

        class Shadow(Timed):
            timer = "host"

    with pytest.raises(IRValidationError):

        class Default(Function):
            timer: Timer = None

    with pytest.raises(IRValidationError):

        class Reserved(Function):
            compile: Timer

    class Host(Function):
        timer: int = 1

    with pytest.raises(IRValidationError):

        class ReplaceHost(Host):
            timer: Timer
