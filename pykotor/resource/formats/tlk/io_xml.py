from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.resource.formats.tlk.data import TLK
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class TLKXMLReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0):
        super().__init__(source, offset)
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(self._reader.read_all().decode())).getroot()
        self._tlk: Optional[TLK] = None

    def load(self) -> TLK:
        self._tlk = TLK()

        # TODO

        self._reader.close()
        return self._tlk


class TLKXMLWriter(ResourceWriter):
    def __init__(self, tlk: TLK, target: TARGET_TYPES):
        super().__init__(target)
        self.xml_root: ElementTree.Element = ElementTree.Element("xml")
        self.tlk: TLK = tlk

    def write(self) -> None:
        # TODO

        ElementTree.indent(self.xml_root)
        self._writer.write_bytes(ElementTree.tostring(self.xml_root))
        self._writer.close()
