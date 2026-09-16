"""Timer ownership, call summaries, branch joins and additive JSON v4 records."""

from dataclasses import replace

import pytest

from .bindings import DeviceBindings, validate_bindings
from .diagnostics import IRValidationError
from .interpreter import Interpreter, ReferenceEnvironment, VirtualClock
from .ir import (
    Call,
    FunctionIR,
    If,
    InputBinding,
    Literal,
    Program,
    Reference,
    ScalarType,
    StartTimer,
    TimerResource,
    Variable,
    VariableRole,
    WaitUntil,
    While,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from .specialization import specialize
from .timing import validate_timer_usage


def program_with(body):
    function = FunctionIR(
        node_id="f",
        name="Timed",
        variables=(
            Variable(node_id="enabled", owner_id="f", name="enabled", type=ScalarType.BOOLEAN, role=VariableRole.INPUT),
        ),
        body=body,
    )
    return Program(
        entry_function_id="f",
        functions=(function,),
        resources=(TimerResource(node_id="timer", owner_id="f", name="timer"),),
    )


def start(identity="start"):
    return StartTimer(node_id=identity, resource_id="timer")


def finish():
    return WaitUntil(
        node_id="finish", resource_id="timer", duration=Literal(node_id="duration", type=ScalarType.DURATION, value=5.0)
    )


def test_branch_join_proves_start_and_specialization_keeps_nondevice_resource():
    program = program_with(
        (
            If(
                node_id="branch",
                condition=Reference(node_id="condition", symbol_id="enabled"),
                then_body=(start("left"),),
                else_body=(start("right"),),
            ),
            finish(),
        )
    )
    document = to_dict(program)
    assert document["format_version"] == 4
    assert document["resources"][0] == {
        "kind": "TimerResource",
        "node_id": "timer",
        "source": None,
        "owner_id": "f",
        "name": "timer",
    }
    before = to_json(program)
    assert validate_bindings(program, DeviceBindings()) == ()
    for candidate in (program, from_json(before), specialize(program, bindings=DeviceBindings())):
        assert validate_timer_usage(candidate) == ()
        for enabled in (True, False):
            clock = VirtualClock()
            result = Interpreter(candidate, environment=ReferenceEnvironment(clock=clock)).run(
                inputs={"enabled": enabled}
            )
            assert clock.monotonic() == 5
            assert result.resources == {}  # Timers never masquerade as devices.
    assert to_json(program) == before


def test_unconditional_and_literal_branches_but_not_zero_iteration_loops_prove_start():
    condition = Literal(node_id="condition", type=ScalarType.BOOLEAN, value=True)
    for body in ((start(), finish()), (If(node_id="if", condition=condition, then_body=(start(),)), finish())):
        assert validate_timer_usage(program_with(body)) == ()
    loop = While(node_id="loop", condition=Reference(node_id="condition", symbol_id="enabled"), body=(start(),))
    assert validate_timer_usage(program_with((loop, finish())))[0].code == "timer_not_started"
    # A definitely unreachable wait is not a required start.
    never = replace(condition, value=False)
    assert validate_timer_usage(program_with((While(node_id="loop", condition=never, body=(finish(),)),))) == ()


def test_unstarted_timer_requirement_propagates_through_nested_calls():
    base = program_with((finish(),))
    # The callee needs an input, so bind a literal false without changing start facts.
    inner = Call(
        node_id="call",
        function_id="f",
        inputs=(
            InputBinding(parameter_id="enabled", value=Literal(node_id="flag", type=ScalarType.BOOLEAN, value=False)),
        ),
    )
    middle = FunctionIR(node_id="middle", name="Middle", body=(inner,))
    outer = FunctionIR(node_id="outer", name="Outer", body=(Call(node_id="outercall", function_id="middle"),))
    program = replace(base, entry_function_id="outer", functions=(*base.functions, middle, outer))
    restored = from_json(to_json(program))
    assert validate_timer_usage(restored)[0].node_id == "finish"
    started = replace(base.functions[0], body=(start(), finish()))
    assert validate_timer_usage(replace(program, functions=(started, middle, outer))) == ()


@pytest.mark.parametrize("change", ["owner", "name", "duplicate", "target", "cross_owner", "duration", "unknown"])
def test_invalid_resource_and_wait_documents_fail_explicitly(change):
    document = to_dict(program_with((start(), finish())))
    resource = document["resources"][0]
    if change == "owner":
        resource["owner_id"] = "missing"
    elif change == "name":
        resource["name"] = "_private"
    elif change == "duplicate":
        document["resources"].append({**resource, "node_id": "second"})
    elif change == "target":
        document["functions"][0]["body"][1]["resource_id"] = "missing"
    elif change == "cross_owner":
        document["functions"].append(
            {"kind": "FunctionIR", "node_id": "other", "source": None, "name": "Other", "variables": [], "body": []}
        )
        resource["owner_id"] = "other"
    elif change == "duration":
        document["functions"][0]["body"][1]["duration"].update(type="real", value=5.0)
    else:
        resource["clock"] = "host"
    with pytest.raises(IRValidationError):
        from_dict(document)
