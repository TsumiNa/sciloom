"""Compare emitted XML to vendor-fixed evidence without changing the evidence."""

import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

from sciloom import Boolean, Function, Integer, compile_ir, runtime
from sciloom.frontend_test import Caller, Counter
from sciloom.ir import IRValidationError, SourceSpan, from_json, to_json

FIXTURES = Path(__file__).resolve().parents[2] / "autosuite/asfp"


class Empty(Function):
    @runtime
    def run(self):
        pass


class Branches(Function):
    def __init__(self):
        self.callee = Empty()

    @runtime
    def run(self):
        if 1 == 1:
            self.callee()
        else:
            self.callee()


class Loop(Function):
    def __init__(self):
        self.callee = Empty()

    @runtime
    def run(self):
        while 0 == 1:
            self.callee()


class Conditional(Function):
    def __init__(self):
        self.callee = Empty()

    @runtime
    def run(self):
        if 1 == 1:
            self.callee()


def normalized(root, names):
    """Keep all structure and binding identity; ignore times and chosen function names."""
    for function in root:
        function.find("name").text = names[function.findtext("name")]
    root[:] = sorted(root, key=lambda f: f.findtext("name"))
    ids = {}

    def visit(element):
        text = (element.text or "").strip()
        if element.tag in ("edittime", "creationtime"):
            text = "timestamp"
        elif re.fullmatch(r"\{[0-9A-Fa-f-]{36}\}", text):
            text = ids.setdefault(text, f"id:{len(ids)}")
        return element.tag, tuple(sorted(element.attrib.items())), text, tuple(visit(c) for c in element)

    return visit(root)


@pytest.mark.parametrize(
    "program,fixture,names",
    [
        (
            Caller(),
            "Test12_FIXED_CallBinding_RealInOut.asfp",
            {
                "Caller": "Caller",
                "Identity": "Callee",
                "TEST12_FIXED_Caller": "Caller",
                "TEST12_FIXED_Callee": "Callee",
            },
        ),
        (
            Branches(),
            "Test10_FIXED3_IfElse_ExactStructure.asfp",
            {
                "Branches": "Caller",
                "Empty": "Callee",
                "TEST10_FIXED3_DirectIFELSE": "Caller",
                "TEST10_FIXED3_Callee": "Callee",
            },
        ),
        (
            Loop(),
            "Test09_DirectWhile_NoOuterMacro.asfp",
            {
                "Loop": "Caller",
                "Empty": "Callee",
                "TEST09_DirectWHILE": "Caller",
                "TEST09_Callee": "Callee",
            },
        ),
        (
            Conditional(),
            "Test08_DirectIf_NoOuterMacro.asfp",
            {
                "Conditional": "Caller",
                "Empty": "Callee",
                "TEST08_DirectIF": "Caller",
                "TEST08_Callee": "Callee",
            },
        ),
    ],
)
def test_structure_and_id_relationships_match_fixed_exports(program, fixture, names):
    result = program.compile()
    assert normalized(ET.fromstring(result.artifact), names) == normalized(
        ET.parse(FIXTURES / fixture).getroot(), names
    )


def test_python_json_compilation_and_write_are_identical(tmp_path):
    program = Caller()
    before = vars(program).copy()
    first = program.compile()
    assert vars(program) == before
    assert first == program.compile()
    assert compile_ir(from_json(to_json(first.semantic_ir))).artifact == first.artifact
    path = first.write(tmp_path / "nested" / "example.asfp")
    assert path.read_bytes() == first.artifact
    assert first.diagnostics == ()


def test_different_specializations_have_disjoint_xml_ids():
    def ids(value):
        return {element.text for element in ET.fromstring(Caller(value).compile().artifact).iter("id")}

    assert ids(2.5).isdisjoint(ids(3.5))


def test_corrupt_call_parameter_is_detected_by_comparison():
    root = ET.fromstring(Caller().compile().artifact)
    call = root.find(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']")
    call.find("functiondata/inputs/item0/id").text = call.findtext("functiondata/outputs/item0/id")
    names = {"Caller": "Caller", "Identity": "Callee", "TEST12_FIXED_Caller": "Caller", "TEST12_FIXED_Callee": "Callee"}
    assert normalized(root, names) != normalized(
        ET.parse(FIXTURES / "Test12_FIXED_CallBinding_RealInOut.asfp").getroot(), names
    )


def test_nested_control_flow_and_boolean_storage():
    class State(Function):
        loop: Integer = 0
        enabled: Boolean = True

        @runtime
        def run(self):
            while self.loop < 2:
                self.loop += 1
                self.enabled = not self.enabled

    root = ET.fromstring(State().compile().artifact)
    boolean = next(v for v in root.iter("variable") if v.findtext("name") == "enabled")
    assert boolean.findtext("value/type") == "11"
    assert boolean.findtext("value/value") == "-1"
    assert boolean.findtext("unit") == "s"
    assert all(e.text != "loop" for e in root.iter("loopvariable"))
    counter = ET.fromstring(Counter().compile().artifact)
    assert len(counter.findall(".//*[@typeid='Chemspeed.SATaskCondition.1']")) == 4


def test_invalid_ir_and_target_fail_before_emission():
    package = Caller().to_ir()
    with pytest.raises(IRValidationError):
        compile_ir(replace(package, entry_function_id="missing"))
    with pytest.raises(ValueError, match="target"):
        Caller().compile(target="unknown")


def test_source_locations_do_not_change_artifact_identity():
    package = Caller().to_ir()
    changed = replace(
        package,
        functions=(
            replace(package.functions[0], source=SourceSpan(path="moved.py", line=100)),
            *package.functions[1:],
        ),
    )
    assert compile_ir(package).artifact == compile_ir(changed).artifact


def test_json_symbol_names_cannot_inject_expressions():
    package = Caller().to_ir()
    caller = package.functions[0]
    changed = replace(
        package,
        functions=(
            replace(caller, variables=(replace(caller.variables[0], name="result + 1"),)),
            *package.functions[1:],
        ),
    )
    root = ET.fromstring(compile_ir(changed).artifact)
    assert root.findtext(".//variable/name") == "v_0"
    assert (
        root.findtext(".//*[@typeid='Chemspeed.SATaskExecuteFunction.1']/functiondata/outputs/item0/variablename")
        == "v_0"
    )


def test_invalid_xml_characters_are_diagnostics():
    package = Caller().to_ir()
    changed = replace(package, functions=(replace(package.functions[0], name="bad\x00name"), *package.functions[1:]))
    with pytest.raises(IRValidationError, match="xml_text"):
        compile_ir(changed)
