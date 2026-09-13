"""Design example only: proposed restricted-Python frontend, not a runnable API."""

from sciloom import Function, Input, Output, Var, Volume, Zone, runtime


class TransferOne(Function):
    source: Input[Zone]
    destination: Input[Zone]
    volume: Input[Volume]
    status: Output[int]

    attempts: Var[int] = 0

    def __init__(self, *, operation_profile="default"):
        # Ordinary Python: compile-time specialization of this instance.
        self.operation_profile = operation_profile

    @runtime
    def run(self):
        self.attempts += 1
        self.status = transfer_volumetrically(
            source=self.source,
            destination=self.destination,
            volume=self.volume,
            profile=self.operation_profile,
        )


program = TransferOne(operation_profile="polymerization")
artifact = program.compile(target="ISYNTH")
