from __future__ import annotations

from contextlib import suppress

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree

try:
    from defusedxml.ElementTree import fromstring as _fromstring
    ElementTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    pass

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.misc import indent


class SSFXMLReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ssf: SSF | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> SSF:
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
    def write(
        self,
        auto_close: bool = True,
    ):
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
