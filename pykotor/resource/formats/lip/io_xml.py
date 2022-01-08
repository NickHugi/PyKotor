from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.resource.formats.lip import LIP, LIPShape
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class LIPXMLReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0):
        super().__init__(source, offset)
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(self._reader.read_all().decode())).getroot()
        self._lip: Optional[LIP] = None

    def load(self) -> LIP:
        if self._xml_root.tag != "lip":
            raise TypeError("The XML file that was loaded was not a valid LIP.")

        self._lip = LIP()

        self._lip.length = float(self._xml_root.get("duration"))

        for subelement in self._xml_root:
            time = float(subelement.get("time"))
            shape = LIPShape(int(subelement.get("shape")))
            self._lip.add(time, shape)

        self._reader.close()
        return self._lip


class LIPXMLWriter(ResourceWriter):
    def __init__(self, lip: LIP, target: TARGET_TYPES):
        super().__init__(target)
        self._lip = lip
        self._xml_root: ElementTree.Element = ElementTree.Element("lip")

    def write(self) -> None:
        self._xml_root.set("duration", str(self._lip.length))

        for keyframe in self._lip:
            ElementTree.SubElement(self._xml_root,
                                   "keyframe",
                                   time=str(keyframe.time),
                                   shape=str(keyframe.shape.value))

        ElementTree.indent(self._xml_root)
        self._writer.write_bytes(ElementTree.tostring(self._xml_root))
        self._writer.close()
