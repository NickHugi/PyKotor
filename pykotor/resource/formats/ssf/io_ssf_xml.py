from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter


class SSFXMLReader(ResourceReader):
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(self._reader.read_bytes(self._size).decode())).getroot()
        self._ssf: Optional[SSF] = None

    def load(self, auto_close: bool = True) -> SSF:
        self._ssf = SSF()

        for child in self._xml_root:
            try:
                sound = SSFSound(int(child.attrib['id']))
                stringref = int(child.attrib['strref'])
                self._ssf.set(sound, stringref)
            except ValueError:
                pass

        if auto_close:
            self._reader.close()

        return self._ssf


class SSFXMLWriter(ResourceWriter):
    def __init__(self, ssf: SSF, target: TARGET_TYPES):
        super().__init__(target)
        self.xml_root: ElementTree.Element = ElementTree.Element("xml")
        self.ssf: SSF = ssf

    def write(self, auto_close: bool = True) -> None:
        for sound_name, sound in SSFSound.__members__.items():
            ElementTree.SubElement(self.xml_root, "sound", {
                "id": str(sound.value),
                "label": sound_name,
                "strref": str(self.ssf.get(sound))
            })

        ElementTree.indent(self.xml_root)
        self._writer.write_bytes(ElementTree.tostring(self.xml_root))

        if auto_close:
            self._writer.close()
