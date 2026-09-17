"""Candidate membership follows well/controller ancestry, never Zone names alone."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from sciloom import Agitator, Function, Input, Zone, at, rpm, runtime
from sciloom.core.bindings import DeviceSelectionBinding
from sciloom.core.diagnostics import CompilationError
from .agitation import AutoSuiteIndividualShaker
from .layout import AutoSuiteLayout
from .layout_test import application, write_app
from .selection import AutoSuiteAgitatorSelection
from .target import AutoSuiteTarget


class Selected(Function):
    mixer: Agitator
    location: Input[Zone]

    @runtime
    def run(self) -> None:
        self.mixer.speed = 300 * rpm
        with at(self.mixer, self.location):
            self.mixer.start()
            self.mixer.stop()


def deployment(tmp_path):
    root = application()
    other = deepcopy(root.find("./configuration/elements/element"))
    other.find("id").text = "00000000-0000-0000-0000-000000000024"
    other.find("deviceid").text = "24"
    block = other.find("./elements/element")
    block.find("id").text = "00000000-0000-0000-0000-000000000102"
    block.find("deviceid").text = "1.2"
    root.find("./configuration/elements").append(other)
    zone = deepcopy(root.find("./zones/zones/zone"))
    zone.find("name").text = "other"
    for well in zone.findall("well"):
        well.set("deviceID", "1.2")
    root.find("./zones/zones").append(zone)
    layout = AutoSuiteLayout.from_app(write_app(tmp_path, root))
    profiles = (
        AutoSuiteIndividualShaker(zone="selected", device_id="23"),
        AutoSuiteIndividualShaker(zone="other", device_id="24"),
    )
    return layout, profiles


def test_layout_resolves_bounded_candidates_but_unverified_native_selection_is_rejected(tmp_path):
    layout, profiles = deployment(tmp_path)
    target = AutoSuiteTarget(layout=layout, devices={"mixer": AutoSuiteAgitatorSelection(candidates=profiles)})
    program = Selected().to_ir()
    (binding,) = target.resolve_devices(program).devices
    assert isinstance(binding, DeviceSelectionBinding)
    assert [candidate.wells for candidate in binding.candidates] == [layout.directory.find(p.zone) for p in profiles]
    assert [c.binding.physical_id for c in binding.candidates] == [
        "autosuite:individual-shaker:23",
        "autosuite:individual-shaker:24",
    ]
    with pytest.raises(CompilationError, match="unsupported_device_location"):
        Selected().compile(target=target)
    with pytest.raises(CompilationError, match="unsupported_device_location"):
        target.emit(program)


def test_supplied_layout_validates_fixed_profiles_without_changing_fixed_output(tmp_path):
    class Fixed(Function):
        mixer: Agitator

        @runtime
        def run(self) -> None:
            self.mixer.speed = 300 * rpm
            self.mixer.start()

    layout, profiles = deployment(tmp_path)
    old = AutoSuiteTarget(devices={"mixer": profiles[0]})
    checked = replace(old, layout=layout)
    assert Fixed().compile(target=old).artifact == Fixed().compile(target=checked).artifact
    with pytest.raises(CompilationError, match="device_selection_binding"):
        Selected().compile(target=checked)
    for bad in (
        replace(profiles[0], device_id="24"),
        replace(profiles[0], device_id="99"),
        replace(profiles[0], zone="absent"),
    ):
        with pytest.raises(ValueError):
            AutoSuiteTarget(devices={"mixer": bad}, layout=layout)


def test_candidate_identity_checks_reject_aliasing_and_nonshaker_ancestry(tmp_path):
    layout, profiles = deployment(tmp_path)
    with pytest.raises(ValueError, match="layout"):
        AutoSuiteTarget(devices={"mixer": AutoSuiteAgitatorSelection(candidates=profiles)})
    for candidates in ((), (profiles[0], profiles[0])):
        with pytest.raises(ValueError):
            AutoSuiteAgitatorSelection(candidates=candidates)
    with pytest.raises(TypeError):
        AutoSuiteAgitatorSelection(candidates=("shaker",))
    with pytest.raises(ValueError, match="physical_id"):
        AutoSuiteTarget(
            layout=layout, devices={"mixer": AutoSuiteAgitatorSelection(candidates=profiles), "other": profiles[0]}
        )
    # Names and addresses still match; replacing the actual controller type fails.
    changed = replace(
        layout, elements=(replace(layout.elements[0], type_id="Chemspeed.SADeviceOther.1"), *layout.elements[1:])
    )
    with pytest.raises(ValueError, match="installed controller"):
        AutoSuiteTarget(layout=changed, devices={"mixer": profiles[0]})
    # One Zone containing wells from both physical controllers is not one device.
    mixed = replace(
        layout.directory,
        zones={
            **layout.directory.zones,
            "mixed": Zone(well_ids=tuple(well for p in profiles for well in layout.directory.find(p.zone).well_ids)),
        },
    )
    with pytest.raises(ValueError, match="does not belong"):
        AutoSuiteTarget(layout=replace(layout, directory=mixed), devices={"mixer": replace(profiles[0], zone="mixed")})


@pytest.mark.requires_corpus
def test_primary_app_candidate_is_derived_from_actual_well_ancestry():
    path = Path(__file__).resolve().parents[4] / "autosuite/corpus/app/config20260909_polymerization.app"
    if not path.exists():
        pytest.skip("Local primary APP is absent.")
    original = path.read_bytes()
    layout = AutoSuiteLayout.from_app(path)
    profile = AutoSuiteIndividualShaker(zone="Heater Shaker 23", device_id="23")
    target = AutoSuiteTarget(layout=layout, devices={"mixer": AutoSuiteAgitatorSelection(candidates=(profile,))})
    (binding,) = target.resolve_devices(Selected().to_ir()).devices
    assert binding.candidates[0].wells == layout.directory.find("Heater Shaker 23")
    with pytest.raises(ValueError, match="does not belong"):
        AutoSuiteTarget(layout=layout, devices={"mixer": replace(profile, device_id="24")})
    assert path.read_bytes() == original
