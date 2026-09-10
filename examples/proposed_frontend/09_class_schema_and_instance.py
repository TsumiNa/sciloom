"""Design example: class schema is known before instantiation; instance holds specialization."""

from sciloom import Function, Input, Output, Zone, Array, Volume, Integer, runtime


class LoadReagent(Function):
    # Static AutoSuite runtime schema: framework registers these at class creation.
    source: Input[Zone]
    destination: Input[Zone]
    volumes: Input[Array[Volume]]
    error_code: Output[Integer] = 0
    index: Integer = 0

    def __init__(self, *, valve_group_size=8):
        # Ordinary Python / host-time state.
        self.valve_group_size = valve_group_size

    @runtime
    def run(self):
        while self.index < len(self.volumes):
            transfer_one(
                source=self.source,
                destination=self.destination,
                volume=self.volumes[self.index],
                valve_group_size=self.valve_group_size,
            )
            self.index += 1


# Available without an instance (illustrative API):
schema = LoadReagent.model_fields

# Concrete specialization:
program = LoadReagent(valve_group_size=8)
result = program.compile(target="ISYNTH")
