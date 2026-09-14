"""Data-only specialization preserves contracts while discarding inactive code."""

import subprocess
import sys
from dataclasses import replace

import pytest

from .bindings import DeviceBindings
from .bindings_test import binding as reference_binding
from .compiler import Artifact, compile_ir
from .diagnostics import CompilationError
from .ir import Call, CanWrite, DeviceIf, FunctionIR, IsDevice, ScalarType, from_json, to_json
from .ir.codec_devices_test import extension_program
from .ir.device_contracts import AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT
from .specialization import specialize


def guarded():
    program = extension_program()
    return replace(
        program,
        resources=(replace(program.resources[0], device_type_id=AGITATOR_CONTRACT.type_id),),
        functions=(
            replace(
                program.functions[0],
                body=(
                    DeviceIf(
                        node_id="if",
                        condition=IsDevice(node_id="query", resource_id="r", device_type_id="test.shaker/v1"),
                        then_body=program.functions[0].body,
                    ),
                ),
            ),
        ),
    )


def basic_bindings():
    return DeviceBindings(devices=(replace(reference_binding(), logical_id="agitator"),))


def test_direct_ir_and_json_select_without_python_device_implementations(tmp_path):
    program = guarded()
    assert specialize(program, bindings=basic_bindings()).functions[0].body == ()
    path = tmp_path / "portable.json"
    path.write_text(to_json(program))
    script = """import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.devices", "sciloom.dsl", "sciloom_autosuite", "examples")):
            raise ImportError("No device implementation package is installed")
sys.meta_path.insert(0, Block())
from pathlib import Path
from sciloom.core.ir import from_json
from sciloom.core.ir.device_contracts import AGITATOR_CONTRACT, BASE_DEVICE_CONTRACT
from sciloom.core.bindings import DeviceBinding, DeviceBindings
from sciloom.core.specialization import specialize
from sciloom.core.interpreter import Interpreter
program = from_json(Path(sys.argv[1]).read_text())
binding = DeviceBinding(logical_id="agitator", physical_id="test", contract=AGITATOR_CONTRACT,
    base_contracts=(BASE_DEVICE_CONTRACT,), writable_properties=AGITATOR_CONTRACT.required_configuration)
selected = specialize(program, bindings=DeviceBindings(devices=(binding,)))
assert selected.functions[0].body == ()
Interpreter(selected).run()
"""
    result = subprocess.run([sys.executable, "-c", script, str(path)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_unreachable_functions_are_pruned_before_target_validation():
    program = guarded()
    condition = program.functions[0].body[0].condition
    helper = FunctionIR(node_id="helper", name="Recursive", body=(Call(node_id="recursive", function_id="helper"),))
    entry = replace(
        program.functions[0],
        body=(DeviceIf(node_id="if", condition=condition, then_body=(Call(node_id="call", function_id="helper"),)),),
    )
    program = replace(program, functions=(entry, helper))

    class Target:
        target_id = "record"
        resolutions = 0

        def resolve_devices(self, program):
            self.resolutions += 1
            return basic_bindings()

        def validate(self, program):
            assert len(program.functions) == 1
            assert not program.functions[0].body
            return ()

        def emit(self, program):
            return Artifact(content=to_json(program).encode(), media_type="application/json", suffix=".json")

    target = Target()
    result = compile_ir(program, target=target)
    assert target.resolutions == 1
    assert len(result.semantic_ir.functions) == 2
    assert from_json(result.artifact.content.decode()) == result.specialized_ir


def test_trusted_ancestry_not_in_authored_directory_is_added():
    program = guarded()
    middle = replace(
        AGITATOR_CONTRACT,
        type_id="vendor.middle/v1",
        base_type_ids=(AGITATOR_CONTRACT.type_id, BASE_DEVICE_CONTRACT.type_id),
    )
    leaf = replace(middle, type_id="vendor.leaf/v1", base_type_ids=(middle.type_id, *middle.base_type_ids))
    binding = replace(
        reference_binding(),
        logical_id="agitator",
        contract=leaf,
        base_contracts=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT, middle),
    )
    selected = specialize(program, bindings=DeviceBindings(devices=(binding,)))
    assert selected.resources[0].device_type_id == leaf.type_id
    assert middle in selected.device_types and leaf in selected.device_types
    with pytest.raises(ValueError, match="ancestor"):
        replace(binding, base_contracts=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT))
    with pytest.raises(ValueError, match="trusted"):
        replace(binding, base_contracts=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT, replace(middle, properties=())))


def test_selected_contract_and_query_signature_must_match_trusted_facts():
    program = guarded()
    contract = program.device_types[-1]
    binding = replace(
        reference_binding(),
        logical_id="agitator",
        contract=contract,
        base_contracts=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT),
    )
    forged = replace(contract, required_configuration=())
    altered = replace(program, device_types=(*program.device_types[:-1], forged))
    with pytest.raises(CompilationError, match="device_contract"):
        specialize(altered, bindings=DeviceBindings(devices=(binding,)))

    # An optional query names a vendor semantic ID but lies about its signature
    # under a different source type ID. A true capability result must not trust it.
    prop = contract.properties[-1]
    trusted = replace(
        contract,
        type_id="trusted.shaker/v1",
        properties=(*contract.properties[:-1], replace(prop, type=ScalarType.INTEGER)),
    )
    binding = replace(binding, contract=trusted, writable_properties=(*binding.writable_properties, prop.semantic_id))
    query = DeviceIf(node_id="if", condition=CanWrite(node_id="query", resource_id="r", property_id=prop.semantic_id))
    program = replace(program, functions=(replace(program.functions[0], body=(query,)),))
    with pytest.raises(CompilationError, match="trusted signature"):
        specialize(program, bindings=DeviceBindings(devices=(binding,)))
