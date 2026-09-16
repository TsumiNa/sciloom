"""For developers: execute volume packing after a source-derived JSON round trip.

Run: ``uv run python -m examples.developer.aspiration_chunk_ir``
Expected terminal output:
    aspiration_chunk_ir.json
    First: next=2, residual=3 mL, aspirate=4.25 mL
    Resumed: next=3, residual=0 mL, aspirate=3.25 mL

The complete source-derived program is aspiration_chunk_ir.json. SourceSpan paths
are explicitly normalized to repository-relative paths for this portable learning
artifact; line positions and semantic fields are preserved. Compilation itself
does not change paths. Repeated reference calls reset working state but reuse the
same session. The caller explicitly supplies the previous residual to resume.
No liquid transfer, device operation or vendor error-handler equivalence is claimed.
"""

from pathlib import Path

from examples.aspiration_chunk import AspirationChunk
from sciloom.core.interpreter import Interpreter
from sciloom.core.ir import from_json, to_json
from sciloom.units import Volume, mL
from .source_paths import repository_relative

if __name__ == "__main__":
    path = Path(__file__).with_suffix(".json")
    path.write_text(to_json(repository_relative(AspirationChunk().to_ir())), encoding="utf-8")
    session = Interpreter(from_json(path.read_text(encoding="utf-8")))
    inputs: dict[str, int | Volume | list[Volume]] = {
        "volumes": [1 * mL, 2 * mL, 4 * mL],
        "start_idx": 0,
        "start_residual": 0 * mL,
        "max_idx": 2,
        "syringe": 5 * mL,
        "airgap": 0.5 * mL,
        "safety": 0.25 * mL,
        "extra": 0.25 * mL,
    }
    first = session.run(inputs=inputs)
    resumed = session.run(
        inputs={**inputs, "start_idx": first.outputs["next_idx"], "start_residual": first.outputs["next_residual"]}
    )
    print(path.name)
    for label, result in (("First", first), ("Resumed", resumed)):
        residual, aspirate = result.outputs["next_residual"], result.outputs["aspirate"]
        assert result.outputs["valid"] and isinstance(residual, Volume) and isinstance(aspirate, Volume)
        print(
            f"{label}: next={result.outputs['next_idx']}, residual={residual / mL:g} mL, aspirate={aspirate / mL:g} mL"
        )
