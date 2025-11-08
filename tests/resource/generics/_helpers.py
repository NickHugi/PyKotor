from __future__ import annotations

from xml.etree import ElementTree as ET


def xml_bytes(xml: str) -> bytes:
    root = ET.fromstring(xml)
    for element in root.iter():
        if element.text is None:
            element.text = ""
    return ET.tostring(root, encoding="utf-8")

