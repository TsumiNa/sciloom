"""Read verified Zone/well addresses and element ancestry from a gzip APP."""

from __future__ import annotations

import gzip
import hashlib
import re
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sciloom.core.locations import LocationDirectory, Well, Zone


@dataclass(frozen=True, kw_only=True)
class AutoSuiteElement:
    """One installed element, retaining its exact parent relation.

    Args:
        identity: Element identity, normalized from its XML UUID by from_app.
        name: Element display name.
        type_id: Observed vendor component type.
        device_id: Vendor address, which is not globally unique across types.
        parent_id: Parent element identity, or None for a root element.
    """

    identity: str
    name: str
    type_id: str
    device_id: str
    parent_id: str | None = None

    def __post_init__(self) -> None:
        for value in (self.identity, self.name, self.type_id, self.device_id):
            if type(value) is not str or not value.strip():
                raise ValueError("Element identity, name, type and address must be nonempty text.")
        if self.parent_id is not None and (type(self.parent_id) is not str or not self.parent_id.strip()):
            raise ValueError("Element parent must be a nonempty identity or None.")


@dataclass(frozen=True, kw_only=True)
class AutoSuiteWell:
    """A stable well identity and its element-local vendor address.

    Args:
        identity: Opaque identity used by semantic Zone values.
        element_id: Owning element identity, not its controller's address.
        well_id: Canonical nonnegative decimal local ID, independent of Zone index.
    """

    identity: str
    element_id: str
    well_id: str

    def __post_init__(self) -> None:
        if any(type(value) is not str or not value.strip() for value in (self.identity, self.element_id)):
            raise ValueError("Well identity and element must be nonempty text.")
        if type(self.well_id) is not str or re.fullmatch(r"0|[1-9][0-9]*", self.well_id) is None:
            raise ValueError("Well IDs must be canonical nonnegative decimal text.")


@dataclass(frozen=True, kw_only=True)
class AutoSuiteLayout:
    """An immutable deployment directory; reading it never imports or runs tasks.

    Args:
        elements: Installed elements with complete, acyclic parent links.
        wells: Element-local addresses corresponding exactly to directory wells.
        directory: Equipment-independent names and ordered Zone memberships.
        app_sha256: Exact APP-byte source hash when read from a file; manual
            layouts default to unknown provenance. Never a semantic identity.

    Raises:
        TypeError: Entries are not immutable typed records.
        ValueError: Identities are duplicated, references unresolved or ancestry cyclic.
    """

    elements: tuple[AutoSuiteElement, ...]
    wells: tuple[AutoSuiteWell, ...]
    directory: LocationDirectory
    app_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.app_sha256 is not None and (
            type(self.app_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", self.app_sha256) is None
        ):
            raise ValueError("app_sha256 must be a lowercase SHA-256 digest or None.")
        if type(self.elements) is not tuple or any(type(item) is not AutoSuiteElement for item in self.elements):
            raise TypeError("Layout elements require an immutable tuple of AutoSuiteElement records.")
        if type(self.wells) is not tuple or any(type(item) is not AutoSuiteWell for item in self.wells):
            raise TypeError("Layout wells require an immutable tuple of AutoSuiteWell records.")
        if type(self.directory) is not LocationDirectory:
            raise TypeError("Layout requires a fixed LocationDirectory.")
        elements = {element.identity: element for element in self.elements}
        if len(elements) != len(self.elements):
            raise ValueError("Layout element identities must be unique.")
        for element in self.elements:
            seen = {element.identity}
            parent = element.parent_id
            while parent is not None:
                if parent not in elements:
                    raise ValueError(f"Unknown element parent {parent!r}.")
                if parent in seen:
                    raise ValueError("Layout element ancestry contains a cycle.")
                seen.add(parent)
                parent = elements[parent].parent_id
        if len({well.identity for well in self.wells}) != len(self.wells):
            raise ValueError("Layout well identities must be unique.")
        if len({(well.element_id, well.well_id) for well in self.wells}) != len(self.wells):
            raise ValueError("Element-local well addresses must be unique.")
        for well in self.wells:
            if well.element_id not in elements:
                raise ValueError(f"Unknown well parent {well.element_id!r}.")
        addresses = {(elements[w.element_id].type_id, elements[w.element_id].device_id, w.well_id) for w in self.wells}
        if len(addresses) != len(self.wells):
            raise ValueError("Layout contains ambiguous vendor well addresses.")
        if {well.identity for well in self.wells} != {well.identity for well in self.directory.wells}:
            raise ValueError("Layout addresses and directory well identities must agree exactly.")

    @classmethod
    def from_app(cls, path: str | Path) -> AutoSuiteLayout:
        """Read a gzip APP's configuration and explicit ordered Zone memberships.

        Args:
            path: Existing application file; no changes are written to it.

        Returns:
            A complete immutable layout preserving element ancestry and Zone order.

        Raises:
            OSError: The file cannot be read.
            ValueError: Gzip/XML, references or the observed layout profile are invalid.

        Only ordinary nonvirtual Zones with explicit zero-based enumeration are
        supported. External base applications are not resolved implicitly. No
        task, calibration or application compilation capability is implied.
        """
        payload = Path(path).read_bytes()
        try:
            root = ET.fromstring(gzip.decompress(payload))
        except (OSError, EOFError, zlib.error, ET.ParseError) as error:
            raise ValueError(f"Expected a gzip-compressed AutoSuite APP: {error}") from error
        if root.tag != "application" or root.get("baseapplication", "").strip():
            raise ValueError("Read a standalone application with no unresolved base application.")
        configuration = root.find("configuration")
        zone_manager = root.find("zones")
        if configuration is None or configuration.get("typeid") != "Chemspeed.SAElementManager.1":
            raise ValueError("APP is missing the observed element-manager configuration.")
        if zone_manager is None or zone_manager.get("typeid") != "Chemspeed.SAZoneManager.1":
            raise ValueError("APP is missing the observed zone manager.")
        if configuration.find("elements") is None or zone_manager.find("zones") is None:
            raise ValueError("APP must contain explicit element and zone collections.")
        elements: list[AutoSuiteElement] = []
        wells: list[AutoSuiteWell] = []
        labels: list[Well] = []
        addresses: dict[tuple[str, str, str], str] = {}

        def read_elements(owner: ET.Element, parent_id: str | None) -> None:
            for node in owner.findall("./elements/element"):
                try:
                    identity = str(UUID(_text(node, "id").strip()))
                except ValueError as error:
                    raise ValueError("APP element identity must be a UUID.") from error
                element = AutoSuiteElement(
                    identity=identity,
                    name=_text(node, "name"),
                    type_id=node.get("typeid", ""),
                    device_id=_text(node, "deviceid"),
                    parent_id=parent_id,
                )
                elements.append(element)
                for raw in node.findall("./wells/well"):
                    local_id = _decimal(_text(raw, "id"))
                    well_identity = f"autosuite:well:{identity}:{local_id}"
                    address = (element.type_id, element.device_id, local_id)
                    if address in addresses:
                        raise ValueError(f"Ambiguous well address {address!r}.")
                    addresses[address] = well_identity
                    wells.append(AutoSuiteWell(identity=well_identity, element_id=identity, well_id=local_id))
                    labels.append(Well(identity=well_identity, name=f"{element.name}: Well #{local_id}"))
                read_elements(node, identity)

        read_elements(configuration, None)
        zones = {}
        for node in zone_manager.findall("./zones/zone"):
            if (
                node.get("typeid") != "Chemspeed.SAZone.1"
                or node.get("virtualVial") != "0"
                or node.get("enumerationType") != "0"
            ):
                raise ValueError("Unsupported Zone profile: require nonvirtual ordinary explicit enumeration.")
            if node.get("enumerationScheme") not in ("0", "1") or node.get("elementEnumerationScheme") not in (
                "0",
                "1",
            ):
                raise ValueError("Unsupported Zone enumeration scheme.")
            name = _text(node, "name")
            if name in zones:
                raise ValueError(f"Duplicate Zone name {name!r}.")
            selected = []
            for index, raw in enumerate(node.findall("well")):
                if _decimal(raw.get("index", "")) != str(index):
                    raise ValueError("Zone members must have consecutive explicit indices in stored order.")
                address = (raw.get("progID", ""), raw.get("deviceID", ""), _decimal(raw.get("id", "")))
                if address not in addresses:
                    raise ValueError(f"Unresolved Zone well address {address!r}.")
                selected.append(addresses[address])
            zones[name] = Zone(well_ids=tuple(selected))
        return cls(
            elements=tuple(elements),
            wells=tuple(wells),
            directory=LocationDirectory(wells=tuple(labels), zones=zones),
            app_sha256=hashlib.sha256(payload).hexdigest(),
        )


def _text(node: ET.Element, field: str) -> str:
    value = node.findtext(field)
    if value is None or not value.strip():
        raise ValueError(f"Missing nonempty layout field {field!r}.")
    return value


def _decimal(value: str) -> str:
    if re.fullmatch(r"[0-9]+", value) is None:
        raise ValueError("Layout well IDs and indices must be nonnegative decimal integers.")
    return str(int(value))
