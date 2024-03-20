from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring
    ElementTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended due to security concerns.")

from typing import TYPE_CHECKING

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.misc import indent

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


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

        data = decode_bytes_with_fallbacks(self._reader.read_bytes(self._reader.size()))
        xml = ElementTree.fromstring(data)  # noqa: S314

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
    ):
        super().__init__(target)
        self._xml: ElementTree.Element = ElementTree.Element("xml")
        self._tlk: TLK = tlk

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        self._xml.tag = "tlk"
        self._xml.set("language", str(self._tlk.language.value))

        for stringref, entry in self._tlk:
            element = ElementTree.Element("string")
            element.text = entry.text
            element.set("id", str(stringref))
            if entry.voiceover:
                element.set("sound", str(entry.voiceover))
            self._xml.append(element)

        indent(self._xml)
        self._writer.write_bytes(ElementTree.tostring(self._xml))
