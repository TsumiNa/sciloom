#!/usr/bin/env python3
import sys, copy, xml.etree.ElementTree as ET
from autosuite_io import load
META={"id","edittime","creationtime","expanded"}
def clean(e):
    for c in list(e):
        if c.tag in META: e.remove(c)
        else: clean(c)
    if e.text is not None:
        e.text=e.text.strip() or None
    e.tail=None
    e.attrib=dict(sorted(e.attrib.items()))
    return e
if __name__=='__main__':
    r=clean(load(sys.argv[1])); ET.indent(r,space='  ')
    ET.ElementTree(r).write(sys.argv[2],encoding='UTF-8',xml_declaration=True)
