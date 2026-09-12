"""Design example: instance construction is host-time specialization; no @comptime."""

from sciloom import Function, Input, Zone, Array, Volume, runtime, Var


class DynamicTransfer(Function):
    source: Input[Zone]
    destination: Input[Zone]
    volumes: Input[Array[Volume]]

    index: Var[int] = 0

    def __init__(self, machine, *, valve_group_size=None, preferred_channels=None):
        # Normal Python executes before compilation.
        self.machine = machine
        self.valve_group_size = (
            valve_group_size
            if valve_group_size is not None
            else machine.isynth.valve_group_size
        )
        self.available_channels = tuple(
            preferred_channels
            if preferred_channels is not None
            else machine.four_needle_head.enabled_channels
        )

    @runtime
    def run(self):
        while self.index < len(self.volumes):
            group_end = valve_group_end(
                self.index,
                group_size=self.valve_group_size,  # specialized Python instance value
            )
            execute_next_chunk(
                source=self.source,
                destination=self.destination,
                volumes=self.volumes,
                start_index=self.index,
                max_index=group_end,
                channels=self.available_channels,
            )
            self.index = next_index()


program8 = DynamicTransfer(machine8)
artifact8 = program8.compile(target=machine8)

program16 = DynamicTransfer(machine16, valve_group_size=16)
artifact16 = program16.compile(target=machine16)
