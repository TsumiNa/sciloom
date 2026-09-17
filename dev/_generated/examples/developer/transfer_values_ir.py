"""Developer example: direct typed flow/length IR, JSON and reference values.

Run: uv run python -m examples.developer.transfer_values_ir
Output:
    transfer_values_ir.json
    Flow: 60.0 mL/min; clearance: 2.0 mm

The complete JSON v4 companion is transfer_values_ir.json. Source and direct IR
produce the same typed outputs; neither emits or executes a native transfer.
"""

from pathlib import Path

from examples.transfer_settings import TransferSettings
from sciloom import FlowRate, Length, mL_per_min, mm
from sciloom.core.bindings import DeviceBindings
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import (
    Assignment,
    Binary,
    BinaryOp,
    FunctionIR,
    Literal,
    Program,
    Reference,
    ScalarType,
    Variable,
    VariableRole,
    from_json,
    to_json,
)
from sciloom.core.specialization import specialize


def build_program() -> Program:
    return Program(
        entry_function_id="f",
        functions=(
            FunctionIR(
                node_id="f",
                name="TransferSettings",
                variables=(
                    Variable(
                        node_id="factor", owner_id="f", name="factor", role=VariableRole.INPUT, type=ScalarType.REAL
                    ),
                    Variable(
                        node_id="flow", owner_id="f", name="flow", role=VariableRole.OUTPUT, type=ScalarType.FLOW_RATE
                    ),
                    Variable(
                        node_id="clearance",
                        owner_id="f",
                        name="clearance",
                        role=VariableRole.OUTPUT,
                        type=ScalarType.LENGTH,
                    ),
                ),
                body=(
                    Assignment(
                        node_id="set_flow",
                        target=Reference(node_id="flow_target", symbol_id="flow"),
                        value=Binary(
                            node_id="scaled",
                            op=BinaryOp.MULTIPLY,
                            left=Reference(node_id="factor_value", symbol_id="factor"),
                            right=Literal(node_id="flow_unit", type=ScalarType.FLOW_RATE, value=1e-6 / 60),
                        ),
                    ),
                    Assignment(
                        node_id="set_clearance",
                        target=Reference(node_id="clearance_target", symbol_id="clearance"),
                        value=Literal(node_id="clearance_value", type=ScalarType.LENGTH, value=0.002),
                    ),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    program = build_program()
    encoded = to_json(program)
    output = Path(__file__).with_suffix(".json")
    output.write_text(encoded)
    result = Interpreter(program).run(inputs={"factor": 60.0})
    for candidate in (TransferSettings().to_ir(), from_json(encoded), specialize(program, bindings=DeviceBindings())):
        assert Interpreter(candidate).run(inputs={"factor": 60.0}).outputs == result.outputs
    print(output.name)
    flow, clearance = result.outputs["flow"], result.outputs["clearance"]
    assert isinstance(flow, FlowRate) and isinstance(clearance, Length)
    print(f"Flow: {flow / mL_per_min:.1f} mL/min; clearance: {clearance / mm:.1f} mm")
