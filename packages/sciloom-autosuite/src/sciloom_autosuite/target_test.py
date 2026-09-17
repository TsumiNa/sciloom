"""Vendor restrictions must not constrain target-independent authoring."""

import pytest

from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError
from sciloom.core.ir import Call, FunctionIR, Program, from_json, to_json, validate
from .agitation import AutoSuiteIndividualShaker
from .deployment import AutoSuiteDeploymentStatus
from .deployment_test import Configure, Stateful, empty_program, facts
from .target import AutoSuiteTarget


def test_deployment_guards_preserve_offline_output_and_report_state_nodes():
    offline = Stateful().compile(target=AutoSuiteTarget())
    compatible = AutoSuiteTarget(deployment=facts())
    assert Stateful().compile(target=compatible).artifact == offline.artifact
    assert compatible.deployment_report(offline.specialized_ir).status == AutoSuiteDeploymentStatus.COMPATIBLE
    assert AutoSuiteTarget().deployment_report(offline.specialized_ir).status == AutoSuiteDeploymentStatus.UNKNOWN
    unknown = AutoSuiteTarget(deployment=facts(reset=None))
    assert Stateful().compile(target=unknown).artifact == offline.artifact
    reset = AutoSuiteTarget(deployment=facts(reset=True))
    with pytest.raises(CompilationError, match="deployment_variable_reset") as error:
        Stateful().compile(target=reset)
    requirements = [d for d in error.value.diagnostics if d.code == "persistent_variable"]
    assert requirements and requirements[0].node_id == offline.specialized_ir.functions[0].variables[0].node_id
    assert compile_ir(empty_program(), target=reset).diagnostics == ()


def test_known_deployment_mismatch_rejects_stateless_programs():
    from dataclasses import replace

    from sciloom.core.locations import LocationDirectory
    from .layout import AutoSuiteLayout

    layout = AutoSuiteLayout(elements=(), wells=(), directory=LocationDirectory(), app_sha256="a" * 64)
    for target, code in (
        (AutoSuiteTarget(deployment=facts(version="3.0")), "deployment_version"),
        (AutoSuiteTarget(deployment=facts(digest="b" * 64), layout=layout), "deployment_source_mismatch"),
    ):
        with pytest.raises(CompilationError, match=code):
            compile_ir(empty_program(), target=target)
    unknown = AutoSuiteTarget(deployment=facts(), layout=replace(layout, app_sha256=None))
    assert unknown.deployment_report(empty_program()).status == AutoSuiteDeploymentStatus.UNKNOWN
    assert compile_ir(empty_program(), target=unknown).diagnostics == ()
    with pytest.raises(TypeError, match="deployment"):
        AutoSuiteTarget(deployment={"reset_variables": False})


def test_configuration_is_guarded_without_user_vars():
    target = AutoSuiteTarget(
        devices={"shaker": AutoSuiteIndividualShaker(zone="bench", device_id="23")}, deployment=facts(reset=True)
    )
    with pytest.raises(CompilationError, match="persistent_device_configuration"):
        Configure().compile(target=target)


def test_list_ir_compiles_to_array_parameters():
    from sciloom.core.ir import ListType, ScalarType, Variable, VariableRole

    variable = Variable(
        node_id="values",
        owner_id="f",
        name="values",
        role=VariableRole.INPUT,
        type=ListType(element_type=ScalarType.REAL),
    )
    program = Program(
        entry_function_id="f", functions=(FunctionIR(node_id="f", name="ListInput", variables=(variable,)),)
    )
    assert validate(program) == ()
    assert b"<isarray>1</isarray>" in compile_ir(program, target=AutoSuiteTarget()).artifact.content


@pytest.mark.parametrize("indirect", [False, True])
def test_recursion_is_legal_ir_but_illegal_for_autosuite(indirect):
    first = FunctionIR(node_id="a", name="A", body=(Call(node_id="call:a", function_id="b" if indirect else "a"),))
    second = FunctionIR(node_id="b", name="B", body=(Call(node_id="call:b", function_id="a"),))
    program = Program(entry_function_id="a", functions=(first, second) if indirect else (first,))
    assert validate(program) == ()
    assert from_json(to_json(program)) == program
    with pytest.raises(CompilationError, match="recursive_call"):
        compile_ir(program, target=AutoSuiteTarget())


def test_unknown_vendor_version():
    with pytest.raises(ValueError):
        AutoSuiteTarget(version="unknown")


def test_unverified_short_circuit_is_rejected_explicitly():
    from sciloom import Function, Output, runtime

    class Logical(Function):
        result: Output[bool]

        @runtime
        def run(self):
            self.result = False and (1 / 0 > 0)

    with pytest.raises(CompilationError, match="unsupported_short_circuit"):
        Logical().compile(target=AutoSuiteTarget())
