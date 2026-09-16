"""For experiment authors: calculate one bounded volume chunk without liquid I/O.

Run: ``uv run python examples/aspiration_chunk.py``
Terminal output: ``AutoSuite volume-list indexing awaits verified runtime guards.``

With volumes [1, 2, 4] mL, a 5 mL syringe, 0.5 mL air gap, 0.25 mL safety
reserve and 0.25 mL extra, usable volume is 4 mL. The first calculation packs
1 + 2 + 1 mL, returns next_idx=2 and residual=3 mL, and requests 4.25 mL total
aspiration. This is arithmetic only, not a dispensing recipe or device operation.

Adapted from Get Aspirate Chunk's capacity/partial-fill calculation and its
caller's four-position boundary. The 1e-12 m^3 tolerance is retained. This example
prevalidates all volume entries and rejects a residual exceeding its requested
volume beyond the tolerance. It returns valid=False with initialized results
for invalid numeric input. It does not implement the vendor global error latch.
Empty/no-work input returns zero volumes and end_idx=start_idx-1. Indices are
zero-based; state is reset each call. See developer/aspiration_chunk_ir.py for
reference results. AutoSuite compilation is currently gated; no ASFP is written.
"""

from math import floor

from sciloom import Function, Input, Output, Var, Volume, mL, runtime, uL
from sciloom.core.diagnostics import CompilationError
from sciloom_autosuite import AutoSuiteTarget


class AspirationChunk(Function):
    """Calculate packing with a residual first item and an inclusive end boundary.

    Attributes:
        volumes: Nonnegative requested volumes for each position.
        start_idx: Position to begin or resume; len(volumes) means no work.
        start_residual: Unfinished volume at start_idx, or zero for a fresh item.
        max_idx: Inclusive caller limit, intersected with the chunk-size boundary.
        syringe: Total volume used for capacity arithmetic.
        airgap: Positive reserved air-gap volume.
        safety: Positive reserved safety volume.
        extra: Positive extra volume added only to a nonempty packed result.
        valid: Whether numeric inputs satisfy this example's preconditions.
        next_idx: Next unfinished position, or one past the last completed one.
        end_idx: Last visited position, or start_idx-1 when nothing was packed.
        end_dispense: Volume assigned to the last visited position.
        next_residual: Unfinished volume for next_idx.
        aspirate: Packed volume plus extra for nonempty work; otherwise zero.
        usable: Capacity after subtracting all three reserves.
        packed: Volume accumulated in this calculation.
        requested: Current position's remaining request.
        remaining: Usable capacity still available.
        dispense: Amount assigned to the current position.
        index: Packing position, explicitly reset each call.
        check_index: Position used to validate all input entries first.
        last_allowed: Inclusive aligned chunk/caller limit.
        active: Whether to examine another position.
    """

    volumes: Input[list[Volume]]
    start_idx: Input[int]
    start_residual: Input[Volume]
    max_idx: Input[int]
    syringe: Input[Volume]
    airgap: Input[Volume]
    safety: Input[Volume]
    extra: Input[Volume]
    valid: Output[bool]
    next_idx: Output[int]
    end_idx: Output[int]
    end_dispense: Output[Volume]
    next_residual: Output[Volume]
    aspirate: Output[Volume]
    usable: Var[Volume] = 0 * mL
    packed: Var[Volume] = 0 * mL
    requested: Var[Volume] = 0 * mL
    remaining: Var[Volume] = 0 * mL
    dispense: Var[Volume] = 0 * mL
    index: Var[int] = 0
    check_index: Var[int] = 0
    last_allowed: Var[int] = 0
    active: Var[bool] = False
    epsilon: Volume = 0.001 * uL

    def __init__(self, *, chunk_size: int = 4) -> None:
        if type(chunk_size) is not int or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive host integer.")
        self.chunk_size = chunk_size

    @runtime
    def run(self) -> None:
        self.valid = True
        self.next_idx = self.start_idx
        self.end_idx = self.start_idx - 1
        self.end_dispense = 0 * mL
        self.next_residual = 0 * mL
        self.aspirate = 0 * mL
        self.packed = 0 * mL
        self.check_index = 0
        while self.check_index < len(self.volumes):
            if self.volumes[self.check_index] < 0 * mL:
                self.valid = False
            self.check_index += 1
        if self.start_idx < 0:
            self.valid = False
        if self.start_idx > len(self.volumes):
            self.valid = False
        if self.start_residual < 0 * mL:
            self.valid = False
        if self.start_idx == len(self.volumes):
            if self.start_residual > self.epsilon:
                self.valid = False
        if self.start_idx < len(self.volumes):
            if self.max_idx < self.start_idx:
                self.valid = False
        if self.valid:
            if self.start_idx < len(self.volumes):
                if self.start_residual > self.volumes[self.start_idx] + self.epsilon:
                    self.valid = False
        if self.syringe <= 0 * mL:
            self.valid = False
        if self.airgap <= 0 * mL:
            self.valid = False
        if self.safety <= 0 * mL:
            self.valid = False
        if self.extra <= 0 * mL:
            self.valid = False
        self.usable = self.syringe - self.airgap - self.extra - self.safety
        if self.usable <= self.epsilon:
            self.valid = False
        self.index = self.start_idx
        self.active = self.valid
        self.last_allowed = -1
        if self.valid:
            self.last_allowed = floor(self.start_idx / self.chunk_size) * self.chunk_size + self.chunk_size - 1
            if self.max_idx < self.last_allowed:
                self.last_allowed = self.max_idx
        while self.active:
            self.active = False
            if self.index < len(self.volumes):
                if self.index <= self.last_allowed:
                    if self.usable - self.packed > self.epsilon:
                        self.requested = self.volumes[self.index]
                        if self.index == self.start_idx:
                            if self.start_residual > self.epsilon:
                                self.requested = self.start_residual
                        self.remaining = self.usable - self.packed
                        if self.requested <= self.remaining + self.epsilon:
                            self.dispense = self.requested
                            if self.dispense > self.remaining:
                                self.dispense = self.remaining
                            self.packed += self.dispense
                            self.end_idx = self.index
                            self.end_dispense = self.dispense
                            self.index += 1
                            self.next_idx = self.index
                            self.next_residual = 0 * mL
                        else:
                            self.dispense = self.remaining
                            self.packed = self.usable
                            self.end_idx = self.index
                            self.end_dispense = self.dispense
                            self.next_idx = self.index
                            self.next_residual = self.requested - self.dispense
                        self.active = True
        if self.valid:
            if self.packed > self.epsilon:
                self.aspirate = self.packed + self.extra


if __name__ == "__main__":
    try:
        AspirationChunk().compile(target=AutoSuiteTarget())
    except CompilationError as error:
        if not error.diagnostics or any(d.code != "unsupported_runtime_guard" for d in error.diagnostics):
            raise
        print("AutoSuite volume-list indexing awaits verified runtime guards.")
    else:
        raise AssertionError("Update this example after native runtime guards are verified.")
