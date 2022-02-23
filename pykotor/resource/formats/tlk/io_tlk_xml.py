from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class TLKXMLReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(self._reader.read_bytes(self._size).decode())).getroot()
        self._tlk: Optional[TLK] = None

    def load(self, auto_close: bool = True) -> TLK:
        self._tlk = TLK()

        # TODO

        if auto_close:
            self._reader.close()

        return self._tlk


class TLKXMLWriter(ResourceWriter):
    def __init__(self, tlk: TLK, target: TARGET_TYPES):
        super().__init__(target)
        self.xml_root: ElementTree.Element = ElementTree.Element("xml")
        self.tlk: TLK = tlk

    def write(self, auto_close: bool = True) -> None:
        # TODO

        ElementTree.indent(self.xml_root)
        self._writer.write_bytes(ElementTree.tostring(self.xml_root))

        if auto_close:
            self._writer.close()
