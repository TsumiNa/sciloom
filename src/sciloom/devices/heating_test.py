"""The heating family uses typed generic effects and no vendor imports."""

import subprocess
import sys
from dataclasses import replace

import pytest

from sciloom import Heater, degC
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import FunctionIR, LifecycleEffect, Program, from_dict, to_dict
from sciloom.core.ir.device_contracts import BASE_DEVICE_CONTRACT, HEATER_CONTRACT
from .declarations import device_contract


def test_heater_contract_and_guarded_author_access():
    assert device_contract(Heater) == HEATER_CONTRACT
    assert HEATER_CONTRACT.operations[0].effect == LifecycleEffect.APPLY_AND_ENABLE
    assert HEATER_CONTRACT.operations[1].effect == LifecycleEffect.DISABLE
    assert len(HEATER_CONTRACT.required_configuration) == 2
    with pytest.raises(TypeError, match="reads"):
        _ = Heater().temperature
    with pytest.raises(TypeError, match="compiled"):
        Heater().temperature = 20 * degC
    with pytest.raises(TypeError, match="compiled"):
        Heater().start()


def test_heater_contract_cannot_be_redefined_by_json():
    program = Program(
        entry_function_id="f",
        functions=(FunctionIR(node_id="f", name="Empty"),),
        device_types=(BASE_DEVICE_CONTRACT, HEATER_CONTRACT),
    )
    document = to_dict(program)
    document["device_types"][1]["operations"][0]["effect"] = "disable"
    with pytest.raises(IRValidationError, match="Built-in"):
        from_dict(document)
    forged = replace(HEATER_CONTRACT, required_configuration=())
    with pytest.raises(IRValidationError, match="Built-in"):
        to_dict(replace(program, device_types=(BASE_DEVICE_CONTRACT, forged)))


def test_heater_import_does_not_load_source_analysis_or_a_target():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.dsl", "sciloom_autosuite")):
            raise ImportError("Device declarations cannot load source or targets")
sys.meta_path.insert(0, Block())
from sciloom import Heater
from sciloom.devices import Heater as DeviceHeater
assert Heater is DeviceHeater
assert Heater.device_type_id == "sciloom.heater/v1"
""",
        ],
        check=True,
    )
