from __future__ import annotations

# Try to import defusedxml, fallback to ET if not available
from xml.etree import ElementTree as ET

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ET.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended for security")

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
    """Reads TLK files from XML format.
    
    XML is a human-readable format for easier editing of talk tables.
    
    References:
    ----------
        vendor/xoreos-tools/src/xml/tlkdumper.cpp (TLK to XML conversion)
        vendor/xoreos-tools/src/xml/tlkcreator.cpp (XML to TLK conversion)
        Note: XML format structure may vary between tools
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._tlk: TLK | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> TLK:  # noqa: FBT001, FBT002, ARG002
        self._tlk = TLK()

        data = decode_bytes_with_fallbacks(self._reader.read_bytes(self._reader.size()))
        xml = ET.fromstring(data)  # noqa: S314

        language = xml.get("language")
        if language is None:
            raise ValueError("The 'language' attribute is missing from the root element of the TLK XML. This attribute is required to specify the language of the TLK file.")
        self._tlk.language = Language(int(language))
        self._tlk.resize(len(xml))
        for string in xml:
            id_str = string.get("id")
            if id_str is None:
                raise ValueError(
                    "The 'id' attribute is missing for a string element in the TLK XML. Each <string>"
                    f" element must have an 'id' attribute to specify its index in the TLK file. Problematic element: {ET.tostring(string, encoding='unicode')}"
                )
            index = int(id_str)

            text = string.text
            if text is None:
                raise ValueError(
                    "The text content is missing for a string element in the TLK XML. Each <string>"
                    f" element must contain text content. Problematic element with id '{id_str}': {ET.tostring(string, encoding='unicode')}"
                )
            self._tlk.entries[index].text = text

            sound = string.get("sound")
            self._tlk.entries[index].voiceover = ResRef(sound) if sound is not None else ResRef.from_blank()

        return self._tlk


class TLKXMLWriter(ResourceWriter):
    def __init__(
        self,
        tlk: TLK,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._xml: ET.Element = ET.Element("xml")
        self._tlk: TLK = tlk

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        self._xml.tag = "tlk"
        self._xml.set("language", str(self._tlk.language.value))

        for stringref, entry in self._tlk:
            element = ET.Element("string")
            element.text = entry.text
            element.set("id", str(stringref))
            if entry.voiceover:
                element.set("sound", str(entry.voiceover))
            self._xml.append(element)

        indent(self._xml)
        self._writer.write_bytes(ET.tostring(self._xml))
