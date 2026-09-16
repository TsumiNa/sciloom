"""Layout import preserves physical ancestry and stored well order without rewriting APP."""

import gzip
import hashlib
import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from sciloom.core.locations import LocationDirectory, Well, Zone
from .layout import AutoSuiteElement, AutoSuiteLayout, AutoSuiteWell

SHAKER = "00000000-0000-0000-0000-000000000023"
BLOCK = "00000000-0000-0000-0000-000000000101"


def application():
    return ET.fromstring(f"""<application baseapplication="">
      <configuration typeid="Chemspeed.SAElementManager.1"><elements>
        <element typeid="Chemspeed.SADeviceIndividualShaker.1">
          <id>{{{SHAKER}}}</id><name>Shaker 23</name><deviceid>23</deviceid>
          <elements><element typeid="Chemspeed.SADeviceISynthBlock2.1">
            <id>{{{BLOCK}}}</id><name>ISynth-2</name><deviceid>1.1</deviceid>
            <wells><well><id>0</id></well><well><id>27</id></well></wells>
          </element></elements>
        </element>
      </elements></configuration>
      <zones typeid="Chemspeed.SAZoneManager.1"><zones>
        <zone typeid="Chemspeed.SAZone.1" virtualVial="0" enumerationType="0" enumerationScheme="1" elementEnumerationScheme="1">
          <name>selected</name>
          <well id="27" deviceID="1.1" progID="Chemspeed.SADeviceISynthBlock2.1" index="0"/>
          <well id="0" deviceID="1.1" progID="Chemspeed.SADeviceISynthBlock2.1" index="1"/>
        </zone>
      </zones></zones>
    </application>""")


def write_app(tmp_path, root):
    path = tmp_path / "layout.app"
    path.write_bytes(gzip.compress(ET.tostring(root)))
    return path


def test_layout_import_preserves_identity_order_ancestry_and_input_bytes(tmp_path):
    path = write_app(tmp_path, application())
    original = path.read_bytes()
    layout = AutoSuiteLayout.from_app(path)
    assert path.read_bytes() == original
    assert len(layout.elements) == len(layout.wells) == 2
    assert layout.elements[1].identity == BLOCK and layout.elements[1].parent_id == SHAKER
    assert layout.elements[0].device_id == "23" and layout.elements[1].device_id == "1.1"
    selected = layout.directory.find("selected")
    wells = {well.identity: well for well in layout.wells}
    assert tuple(wells[identity].well_id for identity in selected.well_ids) == ("27", "0")
    first = Zone(well_ids=(selected.well_ids[0],))
    assert layout.directory.well_name(first) == "ISynth-2: Well #27"
    assert layout.directory.find("absent") == Zone.empty()
    with pytest.raises(FrozenInstanceError):
        layout.elements[0].device_id = "99"


@pytest.mark.parametrize(
    "fault",
    ["unknown", "duplicate_well", "duplicate_zone", "index", "virtual", "enum", "base", "ambiguous", "missing_id"],
)
def test_malformed_layout_never_silently_drops_members(tmp_path, fault):
    root = application()
    zone = root.find("./zones/zones/zone")
    block = root.find("./configuration/elements/element/elements/element")
    if fault == "unknown":
        zone.find("well").set("id", "28")
    elif fault == "duplicate_well":
        zone.findall("well")[1].set("id", "27")
    elif fault == "duplicate_zone":
        root.find("./zones/zones").append(deepcopy(zone))
    elif fault == "index":
        zone.find("well").set("index", "1")
    elif fault == "virtual":
        zone.set("virtualVial", "1")
    elif fault == "enum":
        zone.set("enumerationScheme", "17")
    elif fault == "base":
        root.set("baseapplication", "external.app")
    elif fault == "ambiguous":
        duplicate = deepcopy(block)
        duplicate.find("id").text = "00000000-0000-0000-0000-000000000102"
        root.find("./configuration/elements").append(duplicate)
    else:
        block.remove(block.find("id"))
    with pytest.raises(ValueError):
        AutoSuiteLayout.from_app(write_app(tmp_path, root))


def test_malformed_gzip_xml_and_missing_file_are_distinct(tmp_path):
    path = tmp_path / "invalid.app"
    for content in (b"not gzip", gzip.compress(b"<unclosed>"), gzip.compress(b"<functions/>")):
        path.write_bytes(content)
        with pytest.raises(ValueError):
            AutoSuiteLayout.from_app(path)
    with pytest.raises(FileNotFoundError):
        AutoSuiteLayout.from_app(tmp_path / "missing.app")


def test_direct_layout_checks_ownership_cycles_and_exact_directory_membership(tmp_path):
    layout = AutoSuiteLayout.from_app(write_app(tmp_path, application()))
    for elements, wells, directory in (
        ((layout.elements[0], layout.elements[0]), layout.wells, layout.directory),
        ((replace(layout.elements[0], parent_id=BLOCK), layout.elements[1]), layout.wells, layout.directory),
        ((replace(layout.elements[0], parent_id="missing"), layout.elements[1]), layout.wells, layout.directory),
        (layout.elements, (replace(layout.wells[0], element_id="missing"),), layout.directory),
        (layout.elements, (layout.wells[0], layout.wells[0]), layout.directory),
        (layout.elements, layout.wells, LocationDirectory()),
    ):
        with pytest.raises(ValueError):
            AutoSuiteLayout(elements=elements, wells=wells, directory=directory)
    with pytest.raises(TypeError):
        replace(layout, elements=list(layout.elements))
    extra = AutoSuiteElement(identity="extra", name="Other", type_id=layout.elements[1].type_id, device_id="1.1")
    with pytest.raises(ValueError, match="ambiguous"):
        AutoSuiteLayout(
            elements=(*layout.elements, extra),
            wells=(*layout.wells, AutoSuiteWell(identity="extra:0", element_id="extra", well_id="0")),
            directory=LocationDirectory(
                wells=(*layout.directory.wells, Well(identity="extra:0", name="Other: Well #0"))
            ),
        )


@pytest.mark.requires_corpus
def test_primary_app_resolves_well_27_to_its_actual_shaker_ancestor():
    path = Path(__file__).resolve().parents[4] / "autosuite/corpus/app/config20260909_polymerization.app"
    if not path.exists():
        pytest.skip("Local primary APP is absent.")
    original = hashlib.sha256(path.read_bytes()).digest()
    layout = AutoSuiteLayout.from_app(path)
    zone = layout.directory.find("Heater Shaker 23")
    assert len(zone) == 1
    well = next(well for well in layout.wells if well.identity == zone.well_ids[0])
    elements = {element.identity: element for element in layout.elements}
    owner = elements[well.element_id]
    controller = elements[owner.parent_id]
    assert well.well_id == "27" and owner.device_id == "1.1"
    assert owner.type_id == "Chemspeed.SADeviceISynthBlock2.1"
    assert controller.type_id == "Chemspeed.SADeviceIndividualShaker.1" and controller.device_id == "23"
    assert hashlib.sha256(path.read_bytes()).digest() == original
