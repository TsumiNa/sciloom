"""Individual-shaker deployment and the observed uniform-speed Stir payload.

Task envelope: latest APP / Sample and Run GPC. Concrete zone addressing:
functionsPackage_3.asfp / 1st_vial. Numeric speed is revolutions per second;
speedunit=rpm only selects its display unit. See autosuite/docs/16_AGITATION_MAPPING.md.
"""

import re
from dataclasses import dataclass
from typing import Callable, ClassVar

from sciloom.devices.agitation import Agitator
from .xml import XmlNode, xml_node as _xml


@dataclass(frozen=True, kw_only=True)
class AutoSuiteIndividualShaker(Agitator):
    """Bind one logical controller to a fixed zone on one individual shaker.

    device_id identifies the shaker, not the vessel/rack listed in the zone.
    The caller supplies a matching existing application configuration. This
    record does not discover hardware or establish physical speed limits.
    """

    device_type_id: ClassVar[str] = "sciloom.autosuite.individual-shaker/v1"
    writable_properties: ClassVar[tuple[str, ...]] = ("speed",)
    required_configuration: ClassVar[tuple[str, ...]] = ("speed",)
    supported_operations: ClassVar[tuple[Callable[..., None], ...]] = (Agitator.start, Agitator.stop)
    zone: str
    device_id: str

    def __post_init__(self) -> None:
        for name in ("zone",):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
                raise ValueError(f"{name} must be a nonempty single-line string.")
        if not isinstance(self.device_id, str) or not re.fullmatch(r"[1-9][0-9]*", self.device_id):
            raise ValueError("device_id must be the positive decimal ID of an individual shaker.")


def agitation_task(*, tag: str, binding: AutoSuiteIndividualShaker, speed: str | None, identifier: str) -> XmlNode:
    """Serialize a command; None disables agitation without reading a speed.

    The disabled task retains an inactive editor speed of 100 rpm, as observed
    in the production stop task. This is a wire default, never a commanded
    setpoint or a reconstruction of previous runtime state.
    """
    return _xml(
        tag,
        "",
        _xml("zone", binding.zone),
        _xml("description"),
        _xml("name", "Stir"),
        _xml("edittime", "0"),
        _xml(
            "taskdatas",
            "",
            _xml("count", "1"),
            _xml(
                "taskdata0",
                "",
                _xml("progid", "Chemspeed.SADeviceIndividualShaker.1"),
                _xml("deviceid", binding.device_id),
                _xml("wellid", "-1"),
                _xml("speed", speed if speed is not None else "1.66666666667"),
            ),
        ),
        _xml("switchon", "1" if speed is not None else "0"),
        _xml("speedunit", "rpm"),
        _xml("autofillspeed", "1"),
        _xml("stirrertype", "0"),
        _xml("id", identifier),
        typeid="Chemspeed.SATaskSetAgitation.1",
    )
