"""For developers: associate offline ASFP bytes with explicit deployment requirements.

Run: uv run python -m examples.developer.deployment_review
Expected terminal output:
    Reference totals: 1, 2
    Deployment: unknown; native: pending
    deployment_review.asfp
    deployment_review.deployment.json

Complete generated companions are beside this module. No APP is supplied, so
the report lists the persistent Var requirement and missing deployment facts.
The reference calls specify SciLoom behavior; no Executor or hardware is run.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, runtime
from sciloom.core.interpreter import Interpreter
from sciloom_autosuite import AutoSuiteTarget, write_autosuite_review


class Accumulator(Function):
    amount: Input[int]
    total: Var[int] = 0
    result: Output[int]

    @runtime
    def run(self) -> None:
        self.total += self.amount
        self.result = self.total


if __name__ == "__main__":
    target = AutoSuiteTarget()
    compiled = Accumulator().compile(target=target)
    session = Interpreter(compiled.semantic_ir)
    first = session.run(inputs={"amount": 1}).outputs["result"]
    second = session.run(inputs={"amount": 1}).outputs["result"]
    path = Path(__file__).with_suffix(".asfp")
    report = write_autosuite_review(compiled, target=target, path=path)
    print(f"Reference totals: {first}, {second}")
    print(f"Deployment: {report.status.value}; native: {report.native_status}")
    print(path.name)
    print(path.with_suffix(".deployment.json").name)
