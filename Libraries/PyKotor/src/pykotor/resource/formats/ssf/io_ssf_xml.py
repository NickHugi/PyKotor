from __future__ import annotations

from contextlib import suppress

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ElementTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended for security")

from typing import TYPE_CHECKING

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.misc import indent

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class SSFXMLReader(ResourceReader):
    """Reads SSF files from XML format.
    
    XML is a human-readable format for easier editing of sound set files.
    
    References:
    ----------
        vendor/xoreos-tools/src/xml/ssfdumper.cpp (SSF to XML conversion)
        vendor/xoreos-tools/src/xml/ssfcreator.cpp (XML to SSF conversion)
        Note: XML format structure may vary between tools
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ssf: SSF | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> SSF:  # noqa: FBT001, FBT002, ARG002
        self._ssf = SSF()

        data = decode_bytes_with_fallbacks(self._reader.read_bytes(self._reader.size()))
        xml_root = ElementTree.fromstring(data)  # noqa: S314

        for child in xml_root:
            with suppress(ValueError):
                sound = SSFSound(int(child.attrib["id"]))
                stringref = int(child.attrib["strref"])
                self._ssf.set_data(sound, stringref)

        return self._ssf


class SSFXMLWriter(ResourceWriter):
    def __init__(
        self,
        ssf: SSF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.xml_root: ElementTree.Element = ElementTree.Element("xml")
        self.ssf: SSF = ssf

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        for sound_name, sound in SSFSound.__members__.items():
            ElementTree.SubElement(
                self.xml_root,
                "sound",
                {
                    "id": str(sound.value),
                    "label": sound_name,
                    "strref": str(self.ssf.get(sound)),
                },
            )

        indent(self.xml_root)
        self._writer.write_bytes(ElementTree.tostring(self.xml_root))
