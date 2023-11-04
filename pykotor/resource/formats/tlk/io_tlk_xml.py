from __future__ import annotations

import io
from xml.etree import ElementTree

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
    autoclose,
)
from pykotor.tools.indent_xml import indent


class TLKXMLReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tlk: TLK | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TLK:
        self._tlk = TLK()

        data = self._reader.read_bytes(self._reader.size()).decode()
        xml = ElementTree.parse(io.StringIO(data)).getroot()

        self._tlk.language = Language(int(xml.get("language")))
        self._tlk.resize(len(xml))
        for string in xml:
            index = int(string.get("id"))
            self._tlk.entries[index].text = string.text
            self._tlk.entries[index].voiceover = ResRef(string.get("sound")) if string.get("sound") else ResRef.from_blank()

        return self._tlk


class TLKXMLWriter(ResourceWriter):
    def __init__(
        self,
        tlk: TLK,
        target: TARGET_TYPES,
        strip_soundlength = False,
    ):
        super().__init__(target)
        self._xml: ElementTree.Element = ElementTree.Element("xml")
        self._tlk: TLK = tlk
        self._strip_soundlength = False

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self._xml.tag = "tlk"
        self._xml.set("language", str(self._tlk.language.value))

        for stringref, entry in self._tlk:
            element = ElementTree.Element("string")
            element.text = entry.text
            element.set("id", str(stringref))
            if entry.voiceover:
                element.set("sound", entry.voiceover.get())
            self._xml.append(element)

        indent(self._xml)
        self._writer.write_bytes(ElementTree.tostring(self._xml))
