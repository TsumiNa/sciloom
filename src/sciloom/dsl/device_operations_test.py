"""Device setters are syntax declarations, never host-side hardware actions."""

import pytest

from sciloom import Agitator, Function, Var, rpm, runtime
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import ConfigureProperty, StartAgitation, StopAgitation, from_json, to_json


def test_property_writes_and_explicit_commands_remain_high_level():
    class Sequence(Function):
        agitator: Agitator

        @runtime
        def run(self):
            self.agitator.speed = 0 * rpm
            self.agitator.start()
            self.agitator.stop()

    program = Sequence().to_ir()
    assert [type(node) for node in program.functions[0].body] == [ConfigureProperty, StartAgitation, StopAgitation]
    assert from_json(to_json(program)) == program
    assert program.format_version == 4
    assert "SetAgitation" not in to_json(program)


def test_property_reads_and_augmented_writes_are_rejected():
    class Read(Function):
        agitator: Agitator
        value: Var[float] = 0

        @runtime
        def run(self):
            self.value = self.agitator.speed

    class Augment(Read):
        @runtime
        def run(self):
            self.agitator.speed += 300 * rpm

    class Indexed(Read):
        @runtime
        def run(self):
            self.agitator.speed[0] = 0

    for cls in (Read, Augment, Indexed):
        with pytest.raises(IRValidationError, match="device_property_read"):
            cls().to_ir()


def test_removed_parallel_setter_api_is_rejected():
    class Old(Function):
        agitator: Agitator

        @runtime
        def run(self):
            self.agitator.set_speed(600 * rpm)

    with pytest.raises(IRValidationError, match="unsupported_operation"):
        Old().to_ir()
    assert not hasattr(Agitator, "set_speed")
