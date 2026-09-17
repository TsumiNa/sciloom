"""LiquidHandler is a protected, typed family rather than a native profile."""

import subprocess
import sys
from dataclasses import replace

import pytest

from sciloom import LiquidHandler, Zone, mL, mL_per_min
from sciloom.core.diagnostics import IRValidationError
from sciloom.core.ir import FunctionIR, Program, from_dict, to_dict
from sciloom.core.ir.device_contracts import BASE_DEVICE_CONTRACT, LIQUID_HANDLER_CONTRACT
from .declarations import device_contract


def test_family_contract_and_host_guards():
    assert device_contract(LiquidHandler) == LIQUID_HANDLER_CONTRACT
    assert [p.name for p in LIQUID_HANDLER_CONTRACT.operations[0].parameters] == ["source", "destination", "volume"]
    with pytest.raises(TypeError, match="reads"):
        _ = LiquidHandler().aspirate_flow
    with pytest.raises(TypeError, match="compiled"):
        LiquidHandler().aspirate_flow = 1 * mL_per_min
    with pytest.raises(TypeError, match="compiled"):
        LiquidHandler().transfer(Zone.empty(), Zone.empty(), 1 * mL)


def test_builtin_transfer_contract_cannot_be_redefined_by_json():
    program = Program(
        entry_function_id="f",
        functions=(FunctionIR(node_id="f", name="Empty"),),
        device_types=(BASE_DEVICE_CONTRACT, LIQUID_HANDLER_CONTRACT),
    )
    document = to_dict(program)
    document["device_types"][1]["operations"][0]["parameters"][0]["type"] = "text"
    with pytest.raises(IRValidationError, match="Built-in"):
        from_dict(document)
    with pytest.raises(IRValidationError, match="Built-in"):
        to_dict(
            replace(
                program,
                device_types=(BASE_DEVICE_CONTRACT, replace(LIQUID_HANDLER_CONTRACT, required_configuration=())),
            )
        )


def test_liquid_handler_import_does_not_load_frontend_or_target():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.dsl", "sciloom_autosuite")):
            raise ImportError("Declarations cannot import frontend or target")
sys.meta_path.insert(0, Block())
from sciloom import LiquidHandler
from sciloom.devices import LiquidHandler as Family
assert LiquidHandler is Family
""",
        ],
        check=True,
    )
