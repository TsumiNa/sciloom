"""Immutable target serialization records, separate from semantic IR."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import StrEnum


class AutoSuiteVersion(StrEnum):
    V2_47_1_1 = "autosuite-2.47.1.1"


@dataclass(frozen=True, kw_only=True)
class XmlNode:
    tag: str
    text: str = ""
    attributes: tuple[tuple[str, str], ...] = ()
    children: tuple["XmlNode", ...] = ()

    def to_element(self) -> ET.Element:
        element = ET.Element(self.tag, dict(self.attributes))
        element.text = self.text or None
        element.extend(child.to_element() for child in self.children)
        return element


def xml_node(tag: str, text: str = "", *children: XmlNode, **attributes: str) -> XmlNode:
    """Construct a target record without materializing an XML element."""
    return XmlNode(tag=tag, text=text, attributes=tuple(attributes.items()), children=tuple(children))


@dataclass(frozen=True, kw_only=True)
class SerializationIR:
    target: AutoSuiteVersion
    root: XmlNode

    def to_xml(self) -> bytes:
        element = self.root.to_element()
        ET.indent(element, space="  ")
        return ET.tostring(element, encoding="utf-8", xml_declaration=True) + b"\n"
