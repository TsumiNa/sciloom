"""Design example: native Python control flow lowered to AutoSuite runtime IR."""

from sciloom import Function, Input, Array, Zone, Volume, runtime, Var
from sciloom.units import mL


class DynamicTransfer(Function):
    source_zone: Input[Zone]
    destination_zone: Input[Zone]
    volumes: Input[Array[Volume]]
    max_chunk_size: Input[int]

    index: Var[int] = 0
    remaining: Var[Volume] = 0 * mL
    done: Var[bool] = False

    def __init__(self, *, valve_group_size: int = 8, channels=(1, 2, 3, 4)):
        # Host-time constants/configuration; not AutoSuite runtime fields.
        self.valve_group_size = valve_group_size
        self.channels = tuple(channels)

    @runtime
    def run(self):
        while self.index < len(self.volumes):
            self.remaining = self.volumes[self.index]

            if self.remaining > 0 * mL:
                max_index = valve_group_end(
                    self.index,
                    group_size=self.valve_group_size,
                )
                chunk = get_aspirate_chunk(
                    volumes=self.volumes,
                    start_index=self.index,
                    max_index=max_index,
                    max_chunk_size=self.max_chunk_size,
                    channels=self.channels,
                )

                set_isynth_drawer_valve(
                    destination=self.destination_zone,
                    index=self.index,
                    state="open_for_dispense",
                )

                aspirate_from_source(self.source_zone, chunk.total_volume)
                dispense_chunk(
                    destination=self.destination_zone,
                    start_index=self.index,
                    chunk=chunk,
                )

                self.index = chunk.next_index
            else:
                self.index += 1

        self.done = True


program = DynamicTransfer(valve_group_size=8, channels=(1, 2, 3, 4))
artifact = program.compile(target="ISYNTH")
