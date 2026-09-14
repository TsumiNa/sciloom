"""For SciLoom developers: rebind one JSON program to two device contracts.

Run: uv run python -m examples.developer.portable_agitation

Expected output:
    portable_agitation.json
    AutoSuite: ['speed']
    Demo: ['gain', 'speed']

The same-name JSON keeps both device branches; .autosuite.asfp and .demo.json
are target artifacts. SourceSpan paths are rewritten relative to the repository
root, so every committed companion file is reproducible. The reference interpreter
reports configured parameters, not measured hardware state.
"""

from pathlib import Path

from sciloom import Agitator, Function, Input, RotationalSpeed, comptime, rpm, runtime
from sciloom.core.compiler import compile_ir
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom_autosuite import AutoSuiteIndividualShaker, AutoSuiteTarget
from .demo_contribution import DemoAgitator, DemoTarget
from .source_paths import repository_relative


class PortableAgitation(Function):
    """Apply a demo-only adjustment before the common agitation sequence.

    Attributes:
        agitator: Logical device bound by the selected target.
        speed: Target rotational speed to save and apply.
    """

    agitator: Agitator
    speed: Input[RotationalSpeed]

    @runtime
    def run(self) -> None:
        if comptime.is_device(self.agitator, DemoAgitator):
            self.agitator.gain = 0.5
        self.agitator.speed = self.speed
        self.agitator.start()


if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(repository_relative(PortableAgitation().to_ir())), encoding="utf-8")
    program = from_json(path.read_text(encoding="utf-8"))
    autosuite = compile_ir(
        program,
        target=AutoSuiteTarget(
            devices={
                "agitator": AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23"),
            }
        ),
    )
    demo = compile_ir(program, target=DemoTarget(devices={"agitator": DemoAgitator()}))
    autosuite.write(path.with_suffix(".autosuite.asfp"))
    demo.write(path.with_suffix(".demo.json"))
    print(path.name)
    for name, result in (("AutoSuite", autosuite), ("Demo", demo)):
        snapshot = Interpreter(result.specialized_ir).run(inputs={"speed": 600 * rpm})
        print(f"{name}: {sorted(snapshot.resources['resource:agitator'].configuration)}")
