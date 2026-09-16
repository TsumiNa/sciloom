"""For experiment authors: resolve two named Zones and count their combined wells.

Run: ``uv run python examples/resolve_locations.py``
Expected terminal output: ``resolve_locations.asfp``

The runtime caller supplies two location names. Unknown names give empty Zones;
overlapping wells appear once, in first-occurrence order. The returned Zone is
location data, not a device binding. This program does not move or start hardware.
The complete generated function package is resolve_locations.asfp beside this file.
"""

from pathlib import Path

from sciloom import Function, Input, Output, Var, Zone, runtime, zones
from sciloom_autosuite import AutoSuiteTarget


class ResolveLocations(Function):
    """Combine named sample locations without changing equipment state.

    Attributes:
        first_name: First exact directory name.
        second_name: Second exact directory name.
        selected: Combined ordered selection, independent of later state writes.
        count: Number of distinct selected wells.
        first: Working location value, assigned afresh on every call.
    """

    first_name: Input[str]
    second_name: Input[str]
    selected: Output[Zone]
    count: Output[int]
    first: Var[Zone] = Zone.empty()

    @runtime
    def run(self) -> None:
        self.first = zones.find(self.first_name)
        self.selected = zones.combine(self.first, zones.find(self.second_name))
        self.count = len(self.selected)


if __name__ == "__main__":
    path = ResolveLocations().compile(target=AutoSuiteTarget()).write(Path(__file__).with_suffix(".asfp"))
    print(path.name)
