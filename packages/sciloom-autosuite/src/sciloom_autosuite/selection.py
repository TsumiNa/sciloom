"""Bounded shaker profiles verified against actual APP well/controller ancestry."""

from dataclasses import dataclass

from sciloom.core.bindings import DeviceBinding, DeviceCandidate, DeviceSelectionBinding
from sciloom.devices.declarations import bind_device
from .agitation import AutoSuiteIndividualShaker
from .layout import AutoSuiteLayout


@dataclass(frozen=True, kw_only=True)
class AutoSuiteAgitatorSelection:
    """Declare allowed individual shakers for one runtime-selected logical device.

    Args:
        candidates: Nonempty profiles with distinct shaker IDs and Zone names.

    Raises:
        TypeError: A profile is not an AutoSuiteIndividualShaker.
        ValueError: The selection is empty or repeats a controller/Zone.

    The target requires a layout and verifies real well ancestry. This immutable
    record performs no hardware I/O and does not bypass native failure checks.
    """

    candidates: tuple[AutoSuiteIndividualShaker, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidates", tuple(self.candidates))
        if any(type(profile) is not AutoSuiteIndividualShaker for profile in self.candidates):
            raise TypeError("Candidates must be AutoSuiteIndividualShaker profiles with the same concrete contract.")
        if not self.candidates:
            raise ValueError("A shaker selection requires at least one candidate.")
        for name in ("device_id", "zone"):
            values = [getattr(profile, name) for profile in self.candidates]
            if len(values) != len(set(values)):
                raise ValueError(f"Selection candidates repeat {name}.")


def profile_binding(
    logical_id: str,
    profile: AutoSuiteIndividualShaker | AutoSuiteAgitatorSelection,
    layout: AutoSuiteLayout | None,
) -> DeviceBinding | DeviceSelectionBinding:
    """Resolve known deployment facts without importing or running APP tasks."""
    if isinstance(profile, AutoSuiteAgitatorSelection):
        if layout is None:
            raise ValueError("AutoSuite candidate selection requires an explicit layout.")
        return DeviceSelectionBinding(
            logical_id=logical_id,
            candidates=tuple(_candidate(logical_id, candidate, layout) for candidate in profile.candidates),
        )
    if layout is not None:
        return _candidate(logical_id, profile, layout).binding
    return bind_device(
        logical_id=logical_id, device=profile, physical_id=f"autosuite:individual-shaker:{profile.device_id}"
    )


def _candidate(logical_id: str, profile: AutoSuiteIndividualShaker, layout: AutoSuiteLayout) -> DeviceCandidate:
    selected = layout.directory.find(profile.zone)
    if not selected.well_ids:
        raise ValueError(f"Candidate Zone {profile.zone!r} must exist and contain wells.")
    elements = {element.identity: element for element in layout.elements}
    wells = {well.identity: well for well in layout.wells}
    controllers = [
        element.identity
        for element in layout.elements
        if element.type_id == "Chemspeed.SADeviceIndividualShaker.1" and element.device_id == profile.device_id
    ]
    if len(controllers) != 1:
        raise ValueError(f"Shaker address {profile.device_id!r} must resolve to exactly one installed controller.")
    for identity in selected.well_ids:
        element_id: str | None = wells[identity].element_id
        ancestors = []
        while element_id is not None:
            element = elements[element_id]
            if element.type_id == "Chemspeed.SADeviceIndividualShaker.1":
                ancestors.append(element.identity)
            element_id = element.parent_id
        if ancestors != controllers:
            raise ValueError(
                f"Well {identity!r} does not belong to the declared individual shaker {profile.device_id!r}."
            )
    return DeviceCandidate(
        binding=bind_device(
            logical_id=logical_id, device=profile, physical_id=f"autosuite:individual-shaker:{profile.device_id}"
        ),
        wells=selected,
    )
